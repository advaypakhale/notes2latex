"""LangGraph pipeline: the generate→compile→fix loop."""

import asyncio
import logging
import re
from collections.abc import Awaitable, Callable
from pathlib import Path

from langgraph.config import get_stream_writer
from langgraph.graph import END, StateGraph
from litellm.types.completion import (
    ChatCompletionContentPartImageParam,
    ChatCompletionContentPartTextParam,
    ChatCompletionMessageParam,
    ImageURL,
)
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential

from notes2latex.agent.config import RunConfig
from notes2latex.agent.ingest import load_pages
from notes2latex.agent.prompts import FIX_ERRORS_PROMPT, transcribe_prompt
from notes2latex.agent.state import PipelineState
from notes2latex.clients.llm.client import complete_text
from notes2latex.db.models import JobPhase
from notes2latex.latex.assemble import (
    assemble_document,
    open_environments,
    strip_preamble_from_body,
)
from notes2latex.latex.compile import LatexError, compile_latex
from notes2latex.latex.markers import append_page, page_line_offset

logger = logging.getLogger(__name__)


class Progress(BaseModel):
    """Where a run has got to, reported once per phase change."""

    phase: JobPhase
    current_page: int
    total_pages: int


class PipelineResult(BaseModel):
    total_pages: int
    has_tex: bool
    has_pdf: bool


ProgressCallback = Callable[[Progress], Awaitable[None]]

_CODE_FENCE_RE = re.compile(r"^```(?:latex|tex)?\s*$", re.MULTILINE)

# Transport-level retries for transient provider failures, distinct from the
# LaTeX fix attempts that RunConfig.max_retries governs.
_llm_retry = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    reraise=True,
)


def _strip_code_fences(text: str) -> str:
    return _CODE_FENCE_RE.sub("", text.strip()).strip()


@_llm_retry
async def transcribe_page(
    image_b64: str,
    page_number: int,
    config: RunConfig,
    context_latex: str = "",
) -> str:
    """Send a page image to the VLM and return LaTeX body content."""
    content: list[ChatCompletionContentPartTextParam | ChatCompletionContentPartImageParam] = []

    if context_latex:
        tail = "\n".join(context_latex.splitlines()[-config.context_lines :])
        content.append(
            {
                "type": "text",
                "text": (
                    "Here is the LaTeX body from previous pages (last "
                    f"{config.context_lines} lines):\n```latex\n{tail}\n```\n"
                    "Continue typesetting the next page shown in the image."
                ),
            }
        )

    content.append(
        {
            "type": "text",
            "text": "Typeset the handwritten math notes in this image into LaTeX body content.",
        }
    )
    content.append(
        {
            "type": "image_url",
            "image_url": ImageURL(url=f"data:image/png;base64,{image_b64}", detail="high"),
        }
    )

    messages: list[ChatCompletionMessageParam] = [
        {
            "role": "system",
            "content": transcribe_prompt(page_number, open_environments(context_latex)),
        },
        {"role": "user", "content": content},
    ]

    text = await complete_text(
        model=config.model,
        messages=messages,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
        api_key=config.api_key,
    )
    return _strip_code_fences(text)


@_llm_retry
async def fix_latex(latex_source: str, errors: list[LatexError], config: RunConfig) -> str:
    """Send broken LaTeX and its compile errors to the LLM, and return the corrected source."""
    error_text = "\n".join(
        f"- Line {e.line if e.line is not None else '?'}: {e.message}"
        + (f" (context: {e.context})" if e.context else "")
        for e in errors
    )

    messages: list[ChatCompletionMessageParam] = [
        {"role": "system", "content": FIX_ERRORS_PROMPT},
        {
            "role": "user",
            "content": (
                f"The following LaTeX source has compilation errors:\n\n"
                f"```latex\n{latex_source}\n```\n\n"
                f"Errors:\n{error_text}\n\n"
                f"Return ONLY the corrected complete LaTeX source."
            ),
        },
    ]

    text = await complete_text(
        model=config.model,
        messages=messages,
        temperature=0.0,
        max_tokens=config.max_tokens,
        api_key=config.api_key,
    )
    return _strip_code_fences(text)


def _emit(phase: JobPhase, current_page: int, total_pages: int) -> None:
    get_stream_writer()(Progress(phase=phase, current_page=current_page, total_pages=total_pages))


def _document(state: PipelineState) -> str:
    """Assemble the pages transcribed so far into a compilable document."""
    return assemble_document(state["accumulated_body"], state["config"].preamble)


async def generate_latex_node(state: PipelineState) -> PipelineState:
    config = state["config"]
    page_idx = state["page_index"]
    total = len(state["pages"])

    logger.info("Generating LaTeX for page %d/%d", page_idx + 1, total)
    _emit(JobPhase.TRANSCRIBING, page_idx + 1, total)

    accumulated_body = state["accumulated_body"]
    latex = strip_preamble_from_body(
        await transcribe_page(
            image_b64=state["pages"][page_idx],
            page_number=page_idx + 1,
            config=config,
            context_latex=accumulated_body,
        )
    )

    return {
        "current_page_latex": latex,
        "base_body": accumulated_body,
        "accumulated_body": append_page(page_idx + 1, latex, accumulated_body),
        "retry_count": 0,
    }


async def compile_latex_node(state: PipelineState) -> PipelineState:
    config = state["config"]
    page_idx = state["page_index"]
    total = len(state["pages"])

    _emit(JobPhase.COMPILING, page_idx + 1, total)

    result = await asyncio.to_thread(
        compile_latex, _document(state), config.latex_engine, config.compile_timeout
    )

    if result.success:
        logger.info("Page %d compiled successfully", page_idx + 1)
    else:
        logger.warning(
            "Page %d compile errors: %s",
            page_idx + 1,
            "; ".join(e.message for e in result.errors),
        )

    return {"compiler_success": result.success, "errors": result.errors}


async def fix_latex_node(state: PipelineState) -> PipelineState:
    config = state["config"]
    retry_count = state["retry_count"] + 1
    page_idx = state["page_index"]
    base_body = state["base_body"]

    logger.info("Fix attempt %d for page %d", retry_count, page_idx + 1)
    _emit(JobPhase.FIXING, page_idx + 1, len(state["pages"]))

    # Errors are reported against the whole document, but fix_latex only sees this page.
    offset = page_line_offset(_document(state), page_idx + 1)
    errors = [
        e if e.line is None else e.model_copy(update={"line": max(1, e.line - offset)})
        for e in state["errors"]
    ]

    fixed_page = strip_preamble_from_body(
        await fix_latex(state["current_page_latex"], errors, config)
    )

    return {
        "current_page_latex": fixed_page,
        "accumulated_body": append_page(page_idx + 1, fixed_page, base_body),
        "retry_count": retry_count,
    }


async def advance_page_node(state: PipelineState) -> PipelineState:
    page_idx = state["page_index"]
    # Persist after every page: a failure later on then leaves the pages so far recoverable
    # rather than discarding them with the graph state.
    await asyncio.to_thread(state["config"].outputs.write_tex, _document(state))
    return {"page_index": page_idx + 1, "retry_count": 0}


async def finalize_node(state: PipelineState) -> PipelineState:
    config = state["config"]
    outputs = config.outputs
    total = len(state["pages"])
    _emit(JobPhase.FINALIZING, total, total)

    full_doc = _document(state)
    await asyncio.to_thread(outputs.write_tex, full_doc)

    result = await asyncio.to_thread(
        compile_latex, full_doc, config.latex_engine, config.compile_timeout, outputs.pdf
    )
    if result.log_output:
        await asyncio.to_thread(outputs.write_log, result.log_output)

    has_pdf = result.pdf_path is not None
    if has_pdf:
        logger.info("PDF saved to %s", outputs.pdf)
    else:
        logger.warning("Final compilation failed — only %s was saved", outputs.tex)

    # A streamed graph hands nothing back to its caller, so the outcome leaves on the
    # same channel as the progress updates.
    get_stream_writer()(PipelineResult(total_pages=total, has_tex=True, has_pdf=has_pdf))
    return {}


def route_after_compile(state: PipelineState) -> str:
    if state["compiler_success"]:
        return "advance_page"
    if state["retry_count"] >= state["config"].max_retries:
        logger.warning("Max retries reached for page %d, advancing", state["page_index"] + 1)
        return "advance_page"
    return "fix_latex"


def route_after_advance(state: PipelineState) -> str:
    return "finalize" if state["page_index"] >= len(state["pages"]) else "generate_latex"


def build_graph() -> StateGraph:
    graph = StateGraph(PipelineState)

    graph.add_node("generate_latex", generate_latex_node)
    graph.add_node("compile_latex", compile_latex_node)
    graph.add_node("fix_latex", fix_latex_node)
    graph.add_node("advance_page", advance_page_node)
    graph.add_node("finalize", finalize_node)

    graph.set_entry_point("generate_latex")
    graph.add_edge("generate_latex", "compile_latex")
    graph.add_conditional_edges("compile_latex", route_after_compile)
    graph.add_edge("fix_latex", "compile_latex")
    graph.add_conditional_edges("advance_page", route_after_advance)
    graph.add_edge("finalize", END)

    return graph


def step_budget(page_count: int, max_retries: int) -> int:
    """Return a recursion limit that the graph above cannot legitimately exceed.

    Worst case per page: generate, compile, advance, plus a fix and a compile per retry.
    Then finalize. LangGraph aborts on *reaching* the limit, so one spare superstep is
    added — without it a worst-case run fails after having produced its output.
    """
    return page_count * (3 + 2 * max_retries) + 2


async def run_pipeline(
    file_paths: list[Path], config: RunConfig, on_progress: ProgressCallback | None = None
) -> PipelineResult:
    """Convert the given files, writing the outputs to ``config.output_dir``.

    ``on_progress`` is awaited whenever the run moves to a new phase. A failure anywhere in
    the run propagates as an exception.
    """
    pages = await asyncio.to_thread(load_pages, file_paths, config.dpi, config.max_page_pixels)
    logger.info("Loaded %d page(s) from %d file(s)", len(pages), len(file_paths))
    await asyncio.to_thread(config.outputs.save_page_images, pages)

    initial_state: PipelineState = {
        "pages": pages,
        "config": config,
        "page_index": 0,
        "retry_count": 0,
        "base_body": "",
        "accumulated_body": "",
        "current_page_latex": "",
        "compiler_success": False,
        "errors": [],
    }

    graph = build_graph().compile()
    result: PipelineResult | None = None
    async for update in graph.astream(
        initial_state,
        stream_mode="custom",
        config={"recursion_limit": step_budget(len(pages), config.max_retries)},
    ):
        if isinstance(update, PipelineResult):
            result = update
        elif on_progress is not None:
            await on_progress(update)

    if result is None:
        raise RuntimeError(f"The pipeline stopped before finalizing {len(pages)} page(s)")
    return result
