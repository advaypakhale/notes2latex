"""API routes for job management and conversion."""

import asyncio
import json
import shutil
import uuid
import zipfile
from pathlib import Path
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse, PlainTextResponse
from sqlmodel.ext.asyncio.session import AsyncSession
from sse_starlette.sse import EventSourceResponse

from agent.config import AgentConfig, DEFAULT_PREAMBLE
from agent.graph import run_pipeline
from agent.progress import EventType, ProgressEvent
from agent.utils.page_markers import PAGE_MARKER_RE
from api.v1.agent.models import (
    ConvertRequest,
    JobResponse,
    PageInfo,
    PageLatexResponse,
    PagesResponse,
)
from core.config import get_settings
from db.engine import engine, get_session
from db.repository import JobRepository

router = APIRouter(prefix="/jobs", tags=["jobs"])
preamble_router = APIRouter(prefix="/preamble", tags=["preamble"])

JOBS_DIR = Path("data/jobs")


class JobEventStore:
    """Append-only event log with replayable SSE subscriptions."""

    def __init__(self) -> None:
        self.events: list[ProgressEvent] = []
        self.done: bool = False
        self._condition: asyncio.Condition = asyncio.Condition()

    async def push(self, event: ProgressEvent | None) -> None:
        async with self._condition:
            if event is None:
                self.done = True
            else:
                self.events.append(event)
            self._condition.notify_all()

    async def subscribe(self, from_index: int = 0) -> AsyncGenerator[ProgressEvent, None]:
        idx = from_index
        while True:
            async with self._condition:
                while idx >= len(self.events) and not self.done:
                    await self._condition.wait()

                while idx < len(self.events):
                    yield self.events[idx]
                    idx += 1

                if self.done:
                    return


_event_stores: dict[str, JobEventStore] = {}


def _get_job_dir(job_id: str) -> Path:
    return JOBS_DIR / job_id


@router.post("", response_model=JobResponse)
async def create_job(
    files: list[UploadFile],
    config: str = "{}",
    session: AsyncSession = Depends(get_session),
) -> JobResponse:
    """Create a new conversion job.

    Accepts multipart form with files and a JSON config string.
    """
    req = ConvertRequest.model_validate_json(config)

    job_id = uuid.uuid4().hex[:12]
    job_dir = _get_job_dir(job_id)
    input_dir = job_dir / "input"
    input_dir.mkdir(parents=True, exist_ok=True)
    output_dir = job_dir / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    filenames: list[str] = []
    for f in files:
        if not f.filename:
            continue
        dest = input_dir / f.filename
        content = await f.read()
        dest.write_bytes(content)
        filenames.append(f.filename)

    if not filenames:
        shutil.rmtree(job_dir, ignore_errors=True)
        raise HTTPException(status_code=400, detail="No files uploaded")

    repo = JobRepository(session)
    job = await repo.create(job_id=job_id, model=req.model, filenames=filenames)

    # Build resolved config for this job
    settings = get_settings()
    agent_config = AgentConfig.from_settings(
        settings,
        model=req.model,
        api_key=req.api_key,
        max_retries=req.max_retries,
        dpi=req.dpi,
        preamble=req.preamble,
        output_dir=output_dir,
    )

    # Create event store
    store = JobEventStore()
    _event_stores[job_id] = store

    # Spawn background task
    asyncio.create_task(_run_job(job_id, agent_config, input_dir))

    return JobResponse(
        job_id=job.id,
        status=job.status,
        model=job.model,
        created_at=job.created_at,
        input_filenames=filenames,
    )


async def _run_job(
    job_id: str,
    config: AgentConfig,
    input_dir: Path,
) -> None:
    """Background task that runs the pipeline and pushes events to the store."""
    store = _event_stores.get(job_id)
    output_dir = config.output_dir

    # Events that trigger DB writes
    _DB_EVENTS = {EventType.JOB_STARTED, EventType.JOB_COMPLETED, EventType.JOB_FAILED}

    async def callback(event: ProgressEvent) -> None:
        if store is not None:
            await store.push(event)
        if event.event_type not in _DB_EVENTS:
            return
        async with AsyncSession(engine) as session:
            repo = JobRepository(session)
            if event.event_type == EventType.JOB_STARTED:
                await repo.mark_processing(job_id, event.total_pages)
            elif event.event_type == EventType.JOB_COMPLETED:
                await repo.mark_completed(
                    job_id,
                    has_pdf=(output_dir / "output.pdf").exists(),
                    has_tex=(output_dir / "output.tex").exists(),
                )
            elif event.event_type == EventType.JOB_FAILED:
                await repo.mark_failed(job_id, event.message)

    file_paths = sorted(input_dir.iterdir())

    try:
        await run_pipeline(file_paths, config, callback=callback)
    except Exception as exc:
        async with AsyncSession(engine) as session:
            repo = JobRepository(session)
            await repo.mark_failed(job_id, str(exc))
        if store is not None:
            await store.push(
                ProgressEvent(
                    event_type=EventType.JOB_FAILED,
                    message=str(exc),
                )
            )
    finally:
        # Signal end of stream
        if store is not None:
            await store.push(None)


def _build_job_response(job) -> JobResponse:
    """Convert a DB Job row into an API response."""
    return JobResponse(
        job_id=job.id,
        status=job.status,
        model=job.model,
        total_pages=job.total_pages,
        created_at=job.created_at,
        completed_at=job.completed_at,
        error_message=job.error_message,
        input_filenames=json.loads(job.input_filenames),
        has_pdf=job.has_pdf,
        has_tex=job.has_tex,
    )


@router.get("", response_model=list[JobResponse])
async def list_jobs(
    session: AsyncSession = Depends(get_session),
    limit: int = Query(50, ge=1, le=200),
) -> list[JobResponse]:
    """List recent jobs, newest first."""
    repo = JobRepository(session)
    jobs = await repo.list(limit=limit)
    return [_build_job_response(job) for job in jobs]


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: str,
    session: AsyncSession = Depends(get_session),
) -> JobResponse:
    """Get job status and details."""
    repo = JobRepository(session)
    job = await repo.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return _build_job_response(job)


@router.get("/{job_id}/pages", response_model=PagesResponse)
async def get_job_pages(
    job_id: str,
    session: AsyncSession = Depends(get_session),
) -> PagesResponse:
    """Return page metadata derived from the job's .tex file markers."""
    repo = JobRepository(session)
    job = await repo.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    total_pages = job.total_pages or 0

    # Try to read the .tex file and find page markers
    tex_path = _get_job_dir(job_id) / "output" / "output.tex"
    pages_with_content: set[int] = set()
    if tex_path.exists():
        tex_content = tex_path.read_text(encoding="utf-8")
        for match in PAGE_MARKER_RE.finditer(tex_content):
            pages_with_content.add(int(match.group(1)))

    # If we found markers, use the max marker as total_pages fallback
    if pages_with_content and total_pages == 0:
        total_pages = max(pages_with_content)

    pages = [
        PageInfo(
            page_number=i,
            has_content=i in pages_with_content,
        )
        for i in range(1, total_pages + 1)
    ]

    return PagesResponse(total_pages=total_pages, pages=pages)


@router.get("/{job_id}/events")
async def job_events(job_id: str) -> EventSourceResponse:
    """SSE stream of progress events for a job. Replays all past events then streams live."""
    store = _event_stores.get(job_id)
    if store is None:
        raise HTTPException(status_code=404, detail="No event stream for this job")

    async def event_generator():
        async for event in store.subscribe():
            yield {
                "event": event.event_type.value,
                "data": json.dumps(
                    {
                        "event_type": event.event_type.value,
                        "page": event.page,
                        "total_pages": event.total_pages,
                        "retry": event.retry,
                        "max_retries": event.max_retries,
                        "message": event.message,
                    }
                ),
            }

    return EventSourceResponse(event_generator())


@router.get("/{job_id}/download/{filename}")
async def download_file(
    job_id: str,
    filename: str,
    download: bool = Query(False, description="Force download instead of inline display"),
) -> FileResponse:
    """Download or view an output file from a completed job."""
    job_dir = _get_job_dir(job_id)
    output_dir = job_dir / "output"

    if filename == "all.zip":
        zip_path = output_dir / "all.zip"
        if not zip_path.exists():
            with zipfile.ZipFile(zip_path, "w") as zf:
                for f in output_dir.iterdir():
                    if f.name != "all.zip":
                        zf.write(f, f.name)
        return FileResponse(zip_path, filename="all.zip", media_type="application/zip")

    file_path = output_dir / filename
    if not file_path.exists() or not file_path.is_relative_to(output_dir):
        raise HTTPException(status_code=404, detail="File not found")

    media_types = {
        ".tex": "text/plain",
        ".pdf": "application/pdf",
        ".log": "text/plain",
    }
    media_type = media_types.get(file_path.suffix, "application/octet-stream")

    # Serve inline by default (for PDF preview in iframe), force download if requested
    if download:
        return FileResponse(file_path, filename=filename, media_type=media_type)
    return FileResponse(file_path, media_type=media_type)


@preamble_router.get("/default", response_class=PlainTextResponse)
async def get_default_preamble() -> str:
    """Return the default LaTeX preamble."""
    return DEFAULT_PREAMBLE


# ---------------------------------------------------------------------------
# Page-level endpoints (for side-by-side review)
# ---------------------------------------------------------------------------


def _split_latex_by_page(tex_source: str) -> dict[int, str]:
    """Split a full .tex source into per-page LaTeX using page markers.

    Returns a dict mapping page number (1-based) to that page's body content.
    """
    markers = list(PAGE_MARKER_RE.finditer(tex_source))
    if not markers:
        return {1: tex_source}

    pages: dict[int, str] = {}
    for i, match in enumerate(markers):
        page_num = int(match.group(1))
        start = match.end()
        end = markers[i + 1].start() if i + 1 < len(markers) else len(tex_source)
        pages[page_num] = tex_source[start:end].strip()
    return pages


@router.get("/{job_id}/pages/{page_number}/image")
async def get_page_image(job_id: str, page_number: int) -> FileResponse:
    """Serve the preprocessed page image (PNG) for a specific page."""
    pages_dir = _get_job_dir(job_id) / "output" / "pages"
    image_path = pages_dir / f"page_{page_number:03d}.png"

    if not image_path.exists():
        raise HTTPException(status_code=404, detail=f"Page {page_number} image not found")

    return FileResponse(image_path, media_type="image/png")


@router.get("/{job_id}/pages/{page_number}/latex", response_model=PageLatexResponse)
async def get_page_latex(job_id: str, page_number: int) -> PageLatexResponse:
    """Return the LaTeX source for a specific page, extracted via page markers."""
    tex_path = _get_job_dir(job_id) / "output" / "output.tex"
    if not tex_path.exists():
        raise HTTPException(status_code=404, detail="No .tex output found for this job")

    tex_source = tex_path.read_text(encoding="utf-8")
    pages = _split_latex_by_page(tex_source)

    if page_number not in pages:
        raise HTTPException(status_code=404, detail=f"Page {page_number} not found in LaTeX source")

    return PageLatexResponse(
        job_id=job_id,
        page_number=page_number,
        latex=pages[page_number],
    )
