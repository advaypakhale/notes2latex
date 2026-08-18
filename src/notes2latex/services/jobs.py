"""Job lifecycle: where a job's files live, how its status changes, and how it runs."""

import asyncio
import contextlib
import functools
import logging
import shutil
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from pathlib import Path

from sqlmodel import col, select, update
from sqlmodel.ext.asyncio.session import AsyncSession

from notes2latex.agent.config import RunConfig
from notes2latex.agent.graph import PipelineResult, Progress, run_pipeline
from notes2latex.core.config import get_settings
from notes2latex.core.outputs import JobOutputs
from notes2latex.db.models import Job, JobStatus
from notes2latex.db.session import engine

logger = logging.getLogger(__name__)

JOBS_DIR = get_settings().data_dir / "jobs"
_tasks: dict[str, asyncio.Task] = {}


def job_dir(job_id: str) -> Path:
    return JOBS_DIR / job_id


def input_dir(job_id: str) -> Path:
    return job_dir(job_id) / "input"


def outputs(job_id: str) -> JobOutputs:
    return JobOutputs(job_dir(job_id) / "output")


async def create(session: AsyncSession, job_id: str, model: str, filenames: list[str]) -> Job:
    job = Job(id=job_id, status=JobStatus.PENDING, model=model, input_filenames=filenames)
    session.add(job)
    await session.commit()
    # Commit expires the instance; reload it so the caller can still read its columns.
    await session.refresh(job)
    return job


async def recent(session: AsyncSession, limit: int) -> list[Job]:
    result = await session.exec(select(Job).order_by(col(Job.created_at).desc()).limit(limit))
    return list(result.all())


def start(job_id: str, config: RunConfig, filenames: list[str]) -> None:
    """Run a job in the background, recording its progress on the job row as it goes.

    `filenames` names the job's inputs in the order they should be converted.
    """
    # asyncio keeps only a weak reference to a running task, so hold one until it finishes.
    task = asyncio.create_task(_run(job_id, config, filenames))
    _tasks[job_id] = task
    task.add_done_callback(functools.partial(_on_task_done, job_id))


async def remove(session: AsyncSession, job: Job) -> None:
    """Stop the job if it is still running, then delete its row and its directory."""
    task = _tasks.get(job.id)
    if task is not None:
        task.cancel()
        # Let the runner unwind first: it writes to both the row and the directory.
        with contextlib.suppress(asyncio.CancelledError):
            await task

    await session.delete(job)
    await session.commit()
    await asyncio.to_thread(shutil.rmtree, job_dir(job.id), ignore_errors=True)


def _on_task_done(job_id: str, task: asyncio.Task) -> None:
    _tasks.pop(job_id, None)
    if not task.cancelled() and task.exception() is not None:
        logger.error("Runner for job %s crashed", job_id, exc_info=task.exception())


async def _run(job_id: str, config: RunConfig, filenames: list[str]) -> None:
    paths = [input_dir(job_id) / name for name in filenames]
    try:
        result = await run_pipeline(
            paths, config, on_progress=functools.partial(_record_progress, job_id)
        )
    except Exception as exc:
        logger.exception("Job %s failed", job_id)
        await _record_failure(job_id, str(exc))
    else:
        await _record_completion(job_id, result)


@contextlib.asynccontextmanager
async def _editing(job_id: str) -> AsyncIterator[Job]:
    """Open a job row on its own session, committing whatever the block changed."""
    async with AsyncSession(engine) as session:
        job = await session.get(Job, job_id)
        if job is None:
            msg = f"Unknown job id: {job_id}"
            raise LookupError(msg)
        yield job
        await session.commit()


async def _record_progress(job_id: str, progress: Progress) -> None:
    async with _editing(job_id) as job:
        job.status = JobStatus.PROCESSING
        job.phase = progress.phase
        job.current_page = progress.current_page
        job.total_pages = progress.total_pages


async def _record_completion(job_id: str, result: PipelineResult) -> None:
    async with _editing(job_id) as job:
        job.status = JobStatus.COMPLETED
        job.phase = None
        job.completed_at = datetime.now(UTC)
        job.total_pages = result.total_pages
        job.has_tex = result.has_tex
        job.has_pdf = result.has_pdf


async def _record_failure(job_id: str, message: str) -> None:
    async with _editing(job_id) as job:
        job.status = JobStatus.FAILED
        job.phase = None
        job.completed_at = datetime.now(UTC)
        job.error_message = message


async def recover_interrupted() -> None:
    """Fail jobs left running by a previous process. No runner exists to finish them."""
    async with AsyncSession(engine) as session:
        await session.exec(
            update(Job)
            .where(col(Job.status).in_((JobStatus.PENDING, JobStatus.PROCESSING)))
            .values(
                status=JobStatus.FAILED,
                phase=None,
                completed_at=datetime.now(UTC),
                error_message="Interrupted by a server restart",
            )
        )
        await session.commit()
