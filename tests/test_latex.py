"""Tests for LaTeX compilation, log parsing, and document assembly."""

import shutil

import pytest

from notes2latex.latex.compile import compile_latex, parse_errors
from notes2latex.latex.assemble import assemble_document, open_environments
from notes2latex.agent.prompts import DEFAULT_PREAMBLE

requires_latexmk = pytest.mark.skipif(
    shutil.which("latexmk") is None,
    reason="latexmk not installed",
)


class TestParseErrors:
    def test_no_errors(self):
        log = "This is output\nNo errors here\n"
        assert parse_errors(log) == []

    def test_single_error_with_line(self):
        log = "Some output\n! Undefined control sequence.\nl.42 \\badcommand\nmore output\n"
        errors = parse_errors(log)
        assert len(errors) == 1
        assert errors[0].line == 42
        assert "Undefined control sequence" in errors[0].message

    def test_multiple_errors(self):
        log = (
            "! Missing $ inserted.\n"
            "l.10 some code\n"
            "...\n"
            "! Extra }, or forgotten $.\n"
            "l.25 other code\n"
        )
        errors = parse_errors(log)
        assert len(errors) == 2
        assert errors[0].line == 10
        assert errors[1].line == 25

    def test_error_without_line_number(self):
        log = "! Emergency stop.\n\nsome other text\n"
        errors = parse_errors(log)
        assert len(errors) == 1
        assert errors[0].line is None
        assert "Emergency stop" in errors[0].message

    def test_empty_log(self):
        assert parse_errors("") == []


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
        latex = r"\begin{theorem}" "\n" r"\begin{align}" "\n" r"x &= 1"
        assert open_environments(latex) == ["theorem", "align"]

    def test_partially_closed(self):
        latex = r"\begin{theorem}" "\n" r"\begin{align}" "\n" r"x &= 1" "\n" r"\end{align}"
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
        doc = assemble_document("Hello $x^2$.", DEFAULT_PREAMBLE)
        assert doc.startswith(DEFAULT_PREAMBLE)
        assert "Hello $x^2$." in doc
        assert doc.strip().endswith(r"\end{document}")

    def test_empty_body(self):
        doc = assemble_document("", DEFAULT_PREAMBLE)
        assert r"\begin{document}" in doc
        assert r"\end{document}" in doc


@requires_latexmk
class TestCompileLatex:
    def test_valid_document(self, tmp_path):
        latex = "\\documentclass{article}\n\\begin{document}\nHello $x^2$.\n\\end{document}\n"
        result = compile_latex(latex, pdf_dest=tmp_path / "out.pdf")
        assert result.success
        assert result.pdf_path == tmp_path / "out.pdf"
        assert result.pdf_path.exists()

    def test_invalid_document(self):
        latex = (
            "\\documentclass{article}\n\\begin{document}\n\\undefinedcommandxyz\n\\end{document}\n"
        )
        result = compile_latex(latex)
        assert not result.success
        assert len(result.errors) > 0

    def test_log_output_captured(self):
        latex = "\\documentclass{article}\n\\begin{document}\nHello.\n\\end{document}\n"
        result = compile_latex(latex)
        assert len(result.log_output) > 0
