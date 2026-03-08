"""Application configuration via pydantic-settings."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="NOTES2LATEX_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM settings
    model: str = "ollama/llava"
    api_base: str | None = "http://localhost:11434"
    temperature: float = 0.1
    max_tokens: int = 16384

    # Pipeline settings
    max_retries: int = 3
    context_lines: int = 40  # lines of previous LaTeX to pass as context

    # Output settings
    output_dir: Path = Path("./output")

    # LaTeX settings
    latex_engine: str = "pdflatex"
    compile_timeout: int = 60  # seconds

    # Preprocessing
    dpi: int = 300


@lru_cache
def get_settings() -> Settings:
    """Singleton Settings instance loaded from environment."""
    return Settings()
