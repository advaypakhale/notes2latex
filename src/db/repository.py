"""Job repository — all database operations for job management."""

import json
from datetime import datetime, timezone

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from db.models import Job, JobStatus


class JobRepository:
    """Encapsulates all Job CRUD operations."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, job_id: str, model: str, filenames: list[str]) -> Job:
        job = Job(
            id=job_id,
            status=JobStatus.PENDING,
            model=model,
            input_filenames=json.dumps(filenames),
        )
        self._session.add(job)
        await self._session.commit()
        await self._session.refresh(job)
        return job

    async def get(self, job_id: str) -> Job | None:
        return await self._session.get(Job, job_id)

    async def list(self, limit: int = 50) -> list[Job]:
        result = await self._session.exec(
            select(Job).order_by(Job.created_at.desc()).limit(limit)  # type: ignore[union-attr]
        )
        return list(result.all())

    async def mark_processing(self, job_id: str, total_pages: int) -> None:
        job = await self._require_job(job_id)
        if job is None:
            return
        job.status = JobStatus.PROCESSING
        job.total_pages = total_pages
        await self._session.commit()

    async def mark_completed(self, job_id: str, has_pdf: bool, has_tex: bool) -> None:
        job = await self._require_job(job_id)
        if job is None:
            return
        job.status = JobStatus.COMPLETED
        job.completed_at = datetime.now(timezone.utc)
        job.has_pdf = has_pdf
        job.has_tex = has_tex
        await self._session.commit()

    async def mark_failed(self, job_id: str, error_message: str) -> None:
        job = await self._require_job(job_id)
        if job is None or job.status == JobStatus.FAILED:
            return
        job.status = JobStatus.FAILED
        job.completed_at = datetime.now(timezone.utc)
        job.error_message = error_message
        await self._session.commit()

    async def _require_job(self, job_id: str) -> Job | None:
        """Fetch a job by ID, returning None if not found."""
        return await self._session.get(Job, job_id)
