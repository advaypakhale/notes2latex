"""Route exposing the LaTeX preamble the UI offers as a starting point."""

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from notes2latex.agent.prompts import DEFAULT_PREAMBLE

router = APIRouter(prefix="/preamble", tags=["preamble"])


@router.get("/default", response_class=PlainTextResponse)
async def get_default_preamble() -> str:
    """Return the LaTeX preamble used when a job does not supply its own."""
    return DEFAULT_PREAMBLE
