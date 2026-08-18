"""Assembling a LaTeX document out of model-generated body content."""

import re

_RE_ENV = re.compile(r"\\(begin|end)\{([^}]+)\}")

_PREAMBLE_PREFIXES = (
    r"\documentclass",
    r"\usepackage",
    r"\newtheorem",
    r"\theoremstyle",
    r"\pgfplotsset",
    r"\geometry{",
    r"\declaretheoremstyle",
    r"\declaretheorem",
)

_DOCUMENT_ENV_LINES = frozenset({r"\begin{document}", r"\end{document}"})


def open_environments(latex: str) -> list[str]:
    """Return the environments still open at the end of the string, innermost last."""
    stack: list[str] = []
    for m in _RE_ENV.finditer(latex):
        if m.group(1) == "begin":
            stack.append(m.group(2))
        elif stack and stack[-1] == m.group(2):
            stack.pop()
    return stack


def assemble_document(body: str, preamble: str) -> str:
    r"""Wrap body content in the given preamble, closing anything the body left open.

    A page of transcribed notes routinely ends mid-environment — the transcription prompt
    asks the model to carry environments across page boundaries — so an \end for each is
    emitted before \end{document}.
    """
    closes = "".join(rf"\end{{{env}}}" + "\n" for env in reversed(open_environments(body)))
    return preamble + "\n" + body + "\n" + closes + "\\end{document}\n"


def strip_preamble_from_body(latex: str) -> str:
    """Drop preamble and document-environment lines the model includes in body-only output."""
    return "\n".join(
        line
        for line in latex.splitlines()
        if not (line.strip().startswith(_PREAMBLE_PREFIXES) or line.strip() in _DOCUMENT_ENV_LINES)
    )
