"""Request and response models for the v1 API."""

from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from notes2latex.core.config import Dpi, MaxRetries
from notes2latex.db.models import JobPhase, JobStatus


class ErrorResponse(BaseModel):
    detail: str


# OpenAPI declaration for the 404 every route that looks up a job can return.
NOT_FOUND: dict[int | str, dict] = {404: {"model": ErrorResponse}}


class ConvertRequest(BaseModel):
    """Per-job overrides. Any field left unset falls back to the server's configured default."""

    model: str | None = None
    api_key: str | None = None
    max_retries: MaxRetries | None = None
    dpi: Dpi | None = None
    preamble: str | None = None


class PagesResponse(BaseModel):
    total_pages: int


class JobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    job_id: str = Field(validation_alias="id")
    status: JobStatus
    phase: JobPhase | None
    model: str
    total_pages: int
    current_page: int
    created_at: datetime
    completed_at: datetime | None
    error_message: str | None
    input_filenames: list[str]
    has_pdf: bool
    has_tex: bool

    @field_validator("created_at", "completed_at")
    @classmethod
    def _as_utc(cls, value: datetime | None) -> datetime | None:
        """SQLite stores datetimes without a zone; the stored values are UTC."""
        if value is not None and value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value


class PageLatexResponse(BaseModel):
    job_id: str
    page_number: int
    latex: str
