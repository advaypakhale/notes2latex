"""Pipeline state definitions."""

from pathlib import Path
from typing import Annotated, TypedDict

from agent.config import AgentConfig


def _use_latest(a, b):
    """Reducer that always takes the newer value."""
    return b


class PipelineState(TypedDict, total=False):
    pages: list[str]
    config_dict: Annotated[dict, _use_latest]  # serialized AgentConfig scalars
    page_index: Annotated[int, _use_latest]
    retry_count: Annotated[int, _use_latest]
    # Body content only — no preamble, no \begin/\end{document}
    base_body: Annotated[str, _use_latest]
    accumulated_body: Annotated[str, _use_latest]
    current_page_latex: Annotated[str, _use_latest]
    compiler_success: Annotated[bool, _use_latest]
    errors: Annotated[list[dict], _use_latest]
    output_tex_path: Annotated[str, _use_latest]
    output_pdf_path: Annotated[str, _use_latest]


def get_config(state: PipelineState) -> AgentConfig:
    """Reconstruct AgentConfig from state dict (templates loaded from files)."""
    raw = dict(state.get("config_dict", {}))
    if "output_dir" in raw:
        raw["output_dir"] = Path(raw["output_dir"])
    return AgentConfig(**raw)
