"""Tests for pipeline routing, helpers, and end-to-end flow."""

from unittest.mock import AsyncMock, patch

import pytest

from agent.config import AgentConfig
from agent.graph import route_after_advance, route_after_compile, run_pipeline
from agent.state import PipelineState
from compiler.compiler import CompilerResult
from document.processing import assemble_document, open_environments

# Default preamble loaded from prompts/preamble.tex
_DEFAULT_PREAMBLE = AgentConfig().preamble


class TestRouting:
    def test_route_after_compile_success(self):
        state: PipelineState = {"compiler_success": True, "retry_count": 0, "config_dict": {}}
        assert route_after_compile(state) == "advance"

    def test_route_after_compile_retry(self):
        state: PipelineState = {"compiler_success": False, "retry_count": 1, "config_dict": {}}
        assert route_after_compile(state) == "fix"

    def test_route_after_compile_max_retries(self):
        state: PipelineState = {
            "compiler_success": False,
            "retry_count": 3,
            "config_dict": {},
            "page_index": 0,
        }
        assert route_after_compile(state) == "advance"

    def test_route_after_advance_next_page(self):
        # page_index=1 means we just advanced from page 0; page 1 still needs processing
        state: PipelineState = {"page_index": 1, "pages": ["a", "b", "c"]}
        assert route_after_advance(state) == "next_page"

    def test_route_after_advance_done(self):
        # page_index=3 means all 3 pages (0,1,2) are done
        state: PipelineState = {"page_index": 3, "pages": ["a", "b", "c"]}
        assert route_after_advance(state) == "done"

    def test_route_after_advance_single_page(self):
        # page_index=1 after advancing from the only page
        state: PipelineState = {"page_index": 1, "pages": ["a"]}
        assert route_after_advance(state) == "done"

    def test_route_after_advance_two_pages_midway(self):
        # page_index=1 means page 0 done, page 1 still needs processing
        state: PipelineState = {"page_index": 1, "pages": ["a", "b"]}
        assert route_after_advance(state) == "next_page"


class TestOpenEnvironments:
    def test_empty_string(self):
        assert open_environments("") == []

    def test_no_environments(self):
        assert open_environments(r"Hello $x^2$ world") == []

    def test_closed_environment(self):
        latex = r"\begin{theorem}Some theorem.\end{theorem}"
        assert open_environments(latex) == []

    def test_open_environment(self):
        latex = r"\begin{enumerate}\item First"
        assert open_environments(latex) == ["enumerate"]

    def test_nested_open(self):
        latex = (
            r"\begin{theorem}"
            "\n"
            r"\begin{align}"
            "\n"
            r"x &= 1"
        )
        assert open_environments(latex) == ["theorem", "align"]

    def test_partially_closed(self):
        latex = (
            r"\begin{theorem}"
            "\n"
            r"\begin{align}"
            "\n"
            r"x &= 1"
            "\n"
            r"\end{align}"
        )
        assert open_environments(latex) == ["theorem"]

    def test_multiple_open_close(self):
        latex = (
            r"\begin{theorem}Thm.\end{theorem}"
            "\n"
            r"\begin{proof}"
            "\n"
            r"\begin{align}"
            "\n"
            r"a &= b"
        )
        assert open_environments(latex) == ["proof", "align"]


class TestAssembleDocument:
    def test_assembles_correctly(self):
        body = "Hello $x^2$."
        doc = assemble_document(body, _DEFAULT_PREAMBLE)
        assert doc.startswith(_DEFAULT_PREAMBLE)
        assert "Hello $x^2$." in doc
        assert doc.strip().endswith(r"\end{document}")

    def test_empty_body(self):
        doc = assemble_document("", _DEFAULT_PREAMBLE)
        assert r"\begin{document}" in doc
        assert r"\end{document}" in doc


# Body-only mock (no preamble, no \begin/\end{document})
MOCK_BODY = "Hello $x^2$."


class TestPipelineEndToEnd:
    """Mock-based test for the full pipeline flow."""

    @pytest.mark.asyncio
    async def test_single_page_pipeline(self, tmp_path):
        # Create a dummy image file
        from PIL import Image

        img = Image.new("RGB", (100, 100), color="white")
        img_path = tmp_path / "test.png"
        img.save(img_path)

        config = AgentConfig(output_dir=tmp_path / "output", max_retries=1)

        with (
            patch("agent.graph.transcribe_page", new_callable=AsyncMock) as mock_transcribe,
            patch("agent.graph.compile_latex") as mock_compile,
        ):
            mock_transcribe.return_value = MOCK_BODY

            mock_compile.return_value = CompilerResult(
                success=True,
                pdf_path=None,
                errors=[],
                log_output="",
            )

            result = await run_pipeline([img_path], config)

        # accumulated_body should contain page marker + body content
        assert result["accumulated_body"] == f"% ====== Page 1 ======\n{MOCK_BODY}"
        # The assembled document passed to compile should include preamble
        compile_call_args = mock_compile.call_args_list[0][0][0]
        assert _DEFAULT_PREAMBLE in compile_call_args
        assert r"\end{document}" in compile_call_args
        mock_transcribe.assert_called_once()
        # compile is called in compile_latex_node + finalize_node = 2 times
        assert mock_compile.call_count == 2
