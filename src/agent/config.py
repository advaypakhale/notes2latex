"""Agent configuration — settings, preamble, and prompt templates."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from jinja2 import BaseLoader, Environment

if TYPE_CHECKING:
    from core.config import Settings

_PROMPTS_DIR = Path(__file__).parent / "prompts"
_jinja_env = Environment(loader=BaseLoader())

_SERIALIZABLE_FIELDS = frozenset(
    {
        "model",
        "temperature",
        "max_tokens",
        "max_retries",
        "context_lines",
        "api_key",
        "dpi",
        "latex_engine",
        "compile_timeout",
        "output_dir",
        "preamble",
    }
)


DEFAULT_PREAMBLE = (_PROMPTS_DIR / "preamble.tex").read_text(encoding="utf-8")
DEFAULT_TRANSCRIBE_PROMPT = (_PROMPTS_DIR / "transcribe.md").read_text(encoding="utf-8")


def _load_prompt(name: str) -> str:
    """Read a prompt template by name (without extension) from the prompts directory."""
    return (_PROMPTS_DIR / f"{name}.md").read_text(encoding="utf-8")


@dataclass
class AgentConfig:
    """Configuration for a single pipeline run."""

    # LLM settings
    model: str = "openrouter/google/gemini-3-flash-preview"
    temperature: float = 0.1
    max_tokens: int = 16384

    # Pipeline settings
    max_retries: int = 3
    context_lines: int = 40

    # Runtime
    api_key: str | None = None

    # Output / preprocessing
    output_dir: Path = Path("./output")
    dpi: int = 300

    # Compiler
    latex_engine: str = "pdflatex"
    compile_timeout: int = 60

    # Document settings (loaded from files)
    preamble: str = field(default_factory=lambda: DEFAULT_PREAMBLE)

    # Prompt templates (raw Jinja2 strings, overridable)
    transcribe_template: str = field(default_factory=lambda: _load_prompt("transcribe"))
    fix_errors_template: str = field(default_factory=lambda: _load_prompt("fix_errors"))

    # Metadata
    name: str = "notes2latex"
    version: str = "0.1.0"

    def to_state_dict(self) -> dict:
        """Serialize scalar/path fields for LangGraph state (excludes templates)."""

        def _serialize(val: object) -> object:
            return str(val) if isinstance(val, Path) else val

        return {f: _serialize(getattr(self, f)) for f in _SERIALIZABLE_FIELDS}

    @classmethod
    def from_settings(cls, settings: Settings, **overrides) -> AgentConfig:
        """Build AgentConfig from app Settings with optional per-request overrides."""
        base = {
            "model": settings.model,
            "temperature": settings.temperature,
            "max_tokens": settings.max_tokens,
            "max_retries": settings.max_retries,
            "context_lines": settings.context_lines,
            "output_dir": settings.output_dir,
            "dpi": settings.dpi,
            "latex_engine": settings.latex_engine,
            "compile_timeout": settings.compile_timeout,
        }
        base.update({k: v for k, v in overrides.items() if v is not None})
        return cls(**base)

    def render_transcribe_prompt(self, page_number: int, open_envs: list[str]) -> str:
        """Render the transcription system prompt from stored template."""
        template = _jinja_env.from_string(self.transcribe_template)
        return template.render(page_number=page_number, open_envs=open_envs)

    def render_fix_errors_prompt(self) -> str:
        """Render the fix-errors system prompt from stored template."""
        template = _jinja_env.from_string(self.fix_errors_template)
        return template.render()
