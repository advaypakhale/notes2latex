"""Routes for creating, inspecting, and downloading conversion jobs."""

import asyncio
import io
import shutil
import uuid
import zipfile
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse, Response
from pydantic import ValidationError

from notes2latex.agent.config import RunConfig
from notes2latex.api.deps import JobId, PageNumber, SafeFilename, SessionDep, load_job
from notes2latex.api.v1.schemas import (
    NOT_FOUND,
    ConvertRequest,
    ErrorResponse,
    JobResponse,
    PageLatexResponse,
    PagesResponse,
)
from notes2latex.core.config import get_settings
from notes2latex.latex.markers import page_numbers, split_by_page
from notes2latex.services import jobs

router = APIRouter(prefix="/jobs", tags=["jobs"])

# Multipart form fields cannot nest, so the job config travels as a JSON string. These are the
# OpenAPI 3.1 keywords for describing what that string must contain.
_CONVERT_REQUEST_JSON = {
    "contentMediaType": "application/json",
    "contentSchema": ConvertRequest.model_json_schema(),
}

_UPLOAD_CHUNK = 1 << 20


def _config_errors(exc: ValidationError) -> str:
    """Render a config validation failure without repeating back what was submitted."""
    return "; ".join(
        f"{'.'.join(str(part) for part in error['loc']) or 'config'}: {error['msg']}"
        for error in exc.errors(include_url=False, include_context=False, include_input=False)
    )


def _save_uploads(files: list[UploadFile], input_dir: Path, limit: int) -> list[str]:
    """Stream uploads into input_dir, returning their names in the order they were sent.

    Names are reduced to their last path component. Raises HTTPException if nothing was
    uploaded, for a name that is not a filename, or once the uploads together exceed
    `limit` bytes.
    """
    names: list[str] = []
    remaining = limit
    for upload in files:
        if not upload.filename:
            continue
        # Path().name leaves "" for "/" and ".", and ".." unchanged. Joined onto input_dir
        # those name the directory itself and its parent, neither of which can be opened
        # for writing.
        name = Path(upload.filename).name
        if name in {"", ".."}:
            raise HTTPException(status_code=400, detail=f"Invalid filename: {upload.filename!r}")
        with (input_dir / name).open("wb") as dest:
            while chunk := upload.file.read(_UPLOAD_CHUNK):
                remaining -= len(chunk)
                if remaining < 0:
                    raise HTTPException(
                        status_code=413, detail=f"Uploads exceed the {limit} byte limit"
                    )
                dest.write(chunk)
        names.append(name)
    if not names:
        raise HTTPException(status_code=400, detail="No files uploaded")
    return names


@router.post("", responses={400: {"model": ErrorResponse}, 413: {"model": ErrorResponse}})
async def create_job(
    files: list[UploadFile],
    session: SessionDep,
    config: Annotated[str, Form(json_schema_extra=_CONVERT_REQUEST_JSON)] = "{}",
) -> JobResponse:
    """Upload notes and start converting them.

    The job runs in the background; poll `/api/v1/jobs/{job_id}` for its progress.
    """
    try:
        req = ConvertRequest.model_validate_json(config)
    except ValidationError as exc:
        # `from None`: pydantic renders the offending input into its message, and the config
        # carries the caller's API key. Nothing derived from it may reach the logs.
        raise HTTPException(status_code=400, detail=_config_errors(exc)) from None

    settings = get_settings()
    job_id = uuid.uuid4().hex[:12]
    input_dir = jobs.input_dir(job_id)
    input_dir.mkdir(parents=True, exist_ok=True)
    outputs = jobs.outputs(job_id)
    # The pipeline creates this itself as it writes, but download_archive treats a missing
    # directory as an unknown job, so it has to exist from the moment the job does.
    outputs.dir.mkdir(parents=True, exist_ok=True)

    try:
        filenames = await asyncio.to_thread(
            _save_uploads, files, input_dir, settings.max_upload_bytes
        )
    except HTTPException:
        await asyncio.to_thread(shutil.rmtree, jobs.job_dir(job_id), ignore_errors=True)
        raise

    run_config = RunConfig.from_settings(
        settings, **req.model_dump(exclude_none=True), output_dir=outputs.dir
    )
    job = await jobs.create(session, job_id, model=run_config.model, filenames=filenames)
    jobs.start(job_id, run_config, filenames)

    return JobResponse.model_validate(job)


@router.get("")
async def list_jobs(
    session: SessionDep,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> list[JobResponse]:
    """List recent jobs, newest first."""
    return [JobResponse.model_validate(job) for job in await jobs.recent(session, limit)]


@router.get("/{job_id}", responses=NOT_FOUND)
async def get_job(job_id: JobId, session: SessionDep) -> JobResponse:
    return JobResponse.model_validate(await load_job(session, job_id))


@router.delete("/{job_id}", status_code=204, responses=NOT_FOUND)
async def delete_job(job_id: JobId, session: SessionDep) -> Response:
    """Delete a job, its uploads and its outputs, stopping it first if it is still running."""
    await jobs.remove(session, await load_job(session, job_id))
    return Response(status_code=204)


@router.get("/{job_id}/pages", responses=NOT_FOUND)
async def get_job_pages(job_id: JobId, session: SessionDep) -> PagesResponse:
    """Report the job's page count, falling back to counting page markers in the .tex."""
    job = await load_job(session, job_id)
    if job.total_pages:
        return PagesResponse(total_pages=job.total_pages)

    tex = jobs.outputs(job_id).tex
    written = page_numbers(tex.read_text(encoding="utf-8")) if tex.is_file() else set()
    return PagesResponse(total_pages=max(written, default=0))


@router.get(
    "/{job_id}/download/all.zip",
    response_class=Response,
    responses={200: {"content": {"application/zip": {}}}, **NOT_FOUND},
)
async def download_archive(job_id: JobId) -> Response:
    """Return every output file of a job in one archive."""
    output_dir = jobs.outputs(job_id).dir
    if not output_dir.is_dir():
        raise HTTPException(status_code=404, detail="Job not found")

    return Response(
        content=await asyncio.to_thread(_zip_outputs, output_dir),
        media_type="application/zip",
        headers={"Content-Disposition": 'attachment; filename="all.zip"'},
    )


def _contained_file(base: Path, path: Path) -> Path | None:
    """Resolve path, returning it only if it is a file inside base.

    is_file() follows symlinks on its own, so a link pointing out of base has to be
    rejected by the resolved location rather than by the link.
    """
    resolved = path.resolve()
    return resolved if resolved.is_file() and resolved.is_relative_to(base.resolve()) else None


def _zip_outputs(output_dir: Path) -> bytes:
    buffer = io.BytesIO()
    # Stored rather than deflated: the bulk is a PDF, which is already compressed.
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_STORED) as archive:
        for path in sorted(output_dir.glob("*")):
            target = _contained_file(output_dir, path)
            if target is not None:
                archive.write(target, path.name)
    return buffer.getvalue()


@router.get(
    "/{job_id}/download/{filename}",
    response_class=FileResponse,
    responses={200: {"content": {"application/octet-stream": {}}}, **NOT_FOUND},
)
async def download_file(
    job_id: JobId,
    filename: SafeFilename,
    *,
    download: Annotated[
        bool, Query(description="Send as an attachment rather than inline")
    ] = False,
) -> FileResponse:
    """Serve one output file of a job."""
    output_dir = jobs.outputs(job_id).dir
    file_path = _contained_file(output_dir, output_dir / filename)
    if file_path is None:
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        file_path,
        # Everything else is guessed from the suffix, but .tex maps to text/x-tex, which
        # browsers download instead of previewing.
        media_type="text/plain" if file_path.suffix == ".tex" else None,
        filename=filename if download else None,
    )


@router.get(
    "/{job_id}/pages/{page_number}/image",
    response_class=FileResponse,
    responses={200: {"content": {"image/png": {}}}, **NOT_FOUND},
)
async def get_page_image(job_id: JobId, page_number: PageNumber) -> FileResponse:
    """Serve the rendered source image for a page."""
    image_path = jobs.outputs(job_id).page_image(page_number)
    if not image_path.is_file():
        raise HTTPException(status_code=404, detail=f"Page {page_number} image not found")
    return FileResponse(image_path, media_type="image/png")


@router.get("/{job_id}/pages/{page_number}/latex", responses=NOT_FOUND)
async def get_page_latex(job_id: JobId, page_number: PageNumber) -> PageLatexResponse:
    """Return the LaTeX generated for a single page."""
    tex = jobs.outputs(job_id).tex
    if not tex.is_file():
        raise HTTPException(status_code=404, detail="No .tex output found for this job")

    pages = split_by_page(tex.read_text(encoding="utf-8"))
    if page_number not in pages:
        raise HTTPException(status_code=404, detail=f"Page {page_number} not found in LaTeX source")

    return PageLatexResponse(job_id=job_id, page_number=page_number, latex=pages[page_number])
