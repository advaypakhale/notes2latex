"""Application configuration via pydantic-settings."""

from functools import lru_cache
from pathlib import Path
from typing import Annotated

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

MaxRetries = Annotated[int, Field(ge=0, le=10)]
Dpi = Annotated[int, Field(ge=72, le=1200)]


class RunOptions(BaseModel):
    """Knobs that apply to a conversion run, whether it comes from the CLI or the API."""

    model: str = "openrouter/google/gemini-3-flash-preview"
    temperature: float = Field(default=0.1, ge=0.0, le=2.0)
    max_tokens: int = Field(default=16384, gt=0)

    max_retries: MaxRetries = 3
    context_lines: int = Field(default=40, ge=0)

    output_dir: Path = Path("./output")
    dpi: Dpi = 300
    # A page is rendered into one uncompressed RGB buffer, so this caps a single allocation
    # at three times as many bytes — 180 MB at the default. For scale, US Letter is 8.4 MP
    # at 300 dpi and A2 is 34.8 MP; a dpi past ~600 needs this raised alongside it.
    max_page_pixels: int = Field(default=60_000_000, gt=0)

    latex_engine: str = "pdflatex"
    compile_timeout: int = Field(default=60, gt=0)


class Settings(RunOptions, BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="NOTES2LATEX_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    data_dir: Path = Path("./data")
    # Here rather than in RunOptions because only the API accepts uploads; the CLI reads
    # files the caller already has.
    max_upload_bytes: int = Field(default=100 * 1024 * 1024, gt=0)


@lru_cache
def get_settings() -> Settings:
    return Settings()
