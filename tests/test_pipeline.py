"""Tests for pipeline routing and the end-to-end flow."""

from unittest.mock import AsyncMock, patch

import pytest
from PIL import Image

from notes2latex.latex.compile import CompilerResult
from notes2latex.agent.config import RunConfig
from notes2latex.agent.graph import route_after_advance, route_after_compile, run_pipeline
from notes2latex.agent.prompts import DEFAULT_PREAMBLE
from notes2latex.agent.state import PipelineState

MOCK_BODY = "Hello $x^2$."


class TestRouting:
    def test_route_after_compile_success(self):
        state: PipelineState = {"compiler_success": True, "retry_count": 0, "config": RunConfig()}
        assert route_after_compile(state) == "advance_page"

    def test_route_after_compile_retry(self):
        state: PipelineState = {"compiler_success": False, "retry_count": 1, "config": RunConfig()}
        assert route_after_compile(state) == "fix_latex"

    def test_route_after_compile_max_retries(self):
        state: PipelineState = {
            "compiler_success": False,
            "retry_count": 3,
            "config": RunConfig(),
            "page_index": 0,
        }
        assert route_after_compile(state) == "advance_page"

    def test_route_after_advance_next_page(self):
        # page_index=1 means we just advanced from page 0; page 1 still needs processing
        state: PipelineState = {"page_index": 1, "pages": ["a", "b", "c"]}
        assert route_after_advance(state) == "generate_latex"

    def test_route_after_advance_done(self):
        # page_index=3 means all 3 pages (0,1,2) are done
        state: PipelineState = {"page_index": 3, "pages": ["a", "b", "c"]}
        assert route_after_advance(state) == "finalize"

    def test_route_after_advance_single_page(self):
        state: PipelineState = {"page_index": 1, "pages": ["a"]}
        assert route_after_advance(state) == "finalize"

    def test_route_after_advance_two_pages_midway(self):
        state: PipelineState = {"page_index": 1, "pages": ["a", "b"]}
        assert route_after_advance(state) == "generate_latex"


class TestPipelineEndToEnd:
    @pytest.mark.asyncio
    async def test_single_page_pipeline(self, tmp_path):
        img_path = tmp_path / "test.png"
        Image.new("RGB", (100, 100), color="white").save(img_path)

        config = RunConfig(output_dir=tmp_path / "output", max_retries=1)

        with (
            patch("notes2latex.agent.graph.transcribe_page", new_callable=AsyncMock) as transcribe,
            patch("notes2latex.agent.graph.compile_latex") as compile_latex,
        ):
            transcribe.return_value = MOCK_BODY
            compile_latex.return_value = CompilerResult(success=True)

            result = await run_pipeline([img_path], config)

        assert result.total_pages == 1
        assert result.has_tex and not result.has_pdf

        tex = config.outputs.tex.read_text(encoding="utf-8")
        assert f"% ====== Page 1 ======\n{MOCK_BODY}" in tex
        assert tex.startswith(DEFAULT_PREAMBLE)
        assert tex.strip().endswith(r"\end{document}")

        assert config.outputs.page_image(1).is_file()
        transcribe.assert_called_once()
        # compile_latex_node and finalize_node each compile once.
        assert compile_latex.call_count == 2
