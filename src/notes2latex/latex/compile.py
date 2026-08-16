"""LaTeX compilation and log parsing."""

import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from pydantic import BaseModel

_RE_ERROR = re.compile(r"^! (.+)$", re.MULTILINE)
_RE_LINE_NUM = re.compile(r"^l\.(\d+)\s*(.*)", re.MULTILINE)


class LatexError(BaseModel):
    line: int | None
    message: str
    context: str = ""


class CompilerResult(BaseModel):
    success: bool
    pdf_path: Path | None = None
    errors: list[LatexError] = []
    log_output: str = ""


def compile_latex(
    latex_source: str,
    latex_engine: str = "pdflatex",
    compile_timeout: int = 60,
    pdf_dest: Path | None = None,
) -> CompilerResult:
    """Write latex source to a .tex file, compile with latexmk, and parse the log.

    The compile runs in a scratch directory that is deleted before returning, so copying a
    produced PDF to ``pdf_dest`` — whose parent must already exist — is the only way to
    keep it. ``pdf_path`` is that destination, or None when no PDF survives the call.
    """
    with tempfile.TemporaryDirectory(prefix="notes2latex_") as scratch:
        work_dir = Path(scratch)
        tex_path = work_dir / "output.tex"
        tex_path.write_text(latex_source, encoding="utf-8")

        cmd = [
            "latexmk",
            f"-{latex_engine}",
            "-interaction=nonstopmode",
            "-halt-on-error",
            f"-output-directory={work_dir}",
            # Named relative to cwd below: openin_any=p refuses to open absolute paths, so
            # passing the full path here makes TeX fail to find its own input.
            tex_path.name,
        ]

        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=compile_timeout,
                cwd=str(work_dir),
                # The source can carry a user-supplied preamble, and \input and \openin read
                # any file TeX is allowed to open. TeX Live ships openin_any = a; "p" holds
                # reads to the scratch directory and paths TeX itself considers safe.
                env=os.environ | {"openin_any": "p"},
            )
        except subprocess.TimeoutExpired:
            return CompilerResult(
                success=False,
                errors=[LatexError(line=None, message="Compilation timed out")],
            )

        log_path = work_dir / "output.log"
        log_text = (
            log_path.read_text(encoding="utf-8", errors="replace") if log_path.exists() else ""
        )

        scratch_pdf = work_dir / "output.pdf"
        produced = scratch_pdf.exists()
        if produced and pdf_dest is not None:
            shutil.copy2(scratch_pdf, pdf_dest)

        return CompilerResult(
            success=proc.returncode == 0 and produced,
            pdf_path=pdf_dest if produced else None,
            errors=parse_errors(log_text),
            log_output=log_text,
        )


def parse_errors(log_text: str) -> list[LatexError]:
    """Parse a LaTeX log into errors, splitting it at the '!' markers TeX writes."""
    errors: list[LatexError] = []

    for chunk in re.split(r"(?=^! )", log_text, flags=re.MULTILINE):
        error_match = _RE_ERROR.search(chunk)
        if not error_match:
            continue

        line_match = _RE_LINE_NUM.search(chunk)
        errors.append(
            LatexError(
                line=int(line_match.group(1)) if line_match else None,
                message=error_match.group(1).strip(),
                context=line_match.group(2).strip() if line_match else "",
            )
        )

    return errors
