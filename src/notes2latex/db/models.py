"""Database models for job tracking."""

from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class JobPhase(str, Enum):
    """What a job that is processing is doing to the page it is on."""

    TRANSCRIBING = "transcribing"
    COMPILING = "compiling"
    FIXING = "fixing"
    FINALIZING = "finalizing"


class Job(SQLModel, table=True):
    id: str = Field(primary_key=True)
    status: JobStatus = Field(default=JobStatus.PENDING)
    phase: JobPhase | None = Field(default=None)
    model: str = Field(default="")
    total_pages: int = Field(default=0)
    current_page: int = Field(default=0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = Field(default=None)
    error_message: str | None = Field(default=None)
    input_filenames: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    has_pdf: bool = Field(default=False)
    has_tex: bool = Field(default=False)
