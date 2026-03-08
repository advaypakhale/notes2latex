"""Pydantic request/response models for the agent API."""

from datetime import datetime

from pydantic import BaseModel

from db.models import JobStatus


class ConvertRequest(BaseModel):
    model: str = "ollama/llava"
    api_key: str | None = None
    api_base: str | None = None
    max_retries: int = 3
    dpi: int = 300
    preamble: str | None = None
    transcribe_prompt: str | None = None


class PageInfo(BaseModel):
    page_number: int
    has_content: bool


class PagesResponse(BaseModel):
    total_pages: int
    pages: list[PageInfo]


class JobResponse(BaseModel):
    job_id: str
    status: JobStatus
    model: str = ""
    total_pages: int = 0
    created_at: datetime | None = None
    completed_at: datetime | None = None
    error_message: str | None = None
    input_filenames: list[str] = []
    has_pdf: bool = False
    has_tex: bool = False


class PageLatexResponse(BaseModel):
    job_id: str
    page_number: int
    latex: str
