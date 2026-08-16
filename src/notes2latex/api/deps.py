"""Shared route dependencies and path-parameter types."""

from typing import Annotated

from fastapi import Depends, HTTPException, Path as PathParam
from sqlmodel.ext.asyncio.session import AsyncSession

from notes2latex.db.models import Job
from notes2latex.db.session import get_session

SessionDep = Annotated[AsyncSession, Depends(get_session)]

JobId = Annotated[str, PathParam(pattern=r"^[0-9a-f]{12}$")]
PageNumber = Annotated[int, PathParam(ge=1)]
SafeFilename = Annotated[str, PathParam(pattern=r"^[A-Za-z0-9_-]+\.[A-Za-z0-9]+$")]


async def load_job(session: AsyncSession, job_id: str) -> Job:
    """Fetch a job by id, or raise 404."""
    job = await session.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
