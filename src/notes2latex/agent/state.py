"""LangGraph state for the conversion pipeline."""

from typing import TypedDict

from notes2latex.agent.config import RunConfig
from notes2latex.latex.compile import LatexError


class PipelineState(TypedDict, total=False):
    """Every key is last-write-wins; nodes return only the keys they change.

    The *_body keys hold body content alone — no preamble and no document environment,
    which assemble_document adds at compile time.
    """

    pages: list[str]
    config: RunConfig
    page_index: int
    retry_count: int
    base_body: str
    accumulated_body: str
    current_page_latex: str
    compiler_success: bool
    errors: list[LatexError]
