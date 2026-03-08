"""Database models for job tracking."""

from datetime import datetime, timezone
from enum import Enum

from sqlmodel import Field, SQLModel


class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Job(SQLModel, table=True):
    id: str = Field(primary_key=True)
    status: JobStatus = Field(default=JobStatus.PENDING)
    model: str = Field(default="")
    model_settings: str = Field(default="{}")  # JSON object
    total_pages: int = Field(default=0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = Field(default=None)
    error_message: str | None = Field(default=None)
    input_filenames: str = Field(default="[]")  # JSON list
    has_pdf: bool = Field(default=False)
    has_tex: bool = Field(default=False)
