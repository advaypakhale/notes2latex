"""System prompts and the default LaTeX preamble."""

from pathlib import Path

from jinja2 import Environment

_DIR = Path(__file__).parent


def _read(name: str) -> str:
    return (_DIR / name).read_text(encoding="utf-8")


DEFAULT_PREAMBLE = _read("preamble.tex")
FIX_ERRORS_PROMPT = _read("fix_errors.md")

_TRANSCRIBE_TEMPLATE = Environment().from_string(_read("transcribe.md"))


def transcribe_prompt(page_number: int, open_envs: list[str]) -> str:
    """Render the transcription prompt for a page, given environments left open by earlier pages."""
    return _TRANSCRIBE_TEMPLATE.render(page_number=page_number, open_envs=open_envs)
