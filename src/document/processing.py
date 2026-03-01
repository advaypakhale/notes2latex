"""Document processing — LaTeX assembly, environment tracking, and cleanup."""

import re

_RE_ENV = re.compile(r"\\(begin|end)\{([^}]+)\}")


def open_environments(latex: str) -> list[str]:
    """Return stack of environments still open at end of the string."""
    stack: list[str] = []
    for m in _RE_ENV.finditer(latex):
        if m.group(1) == "begin":
            stack.append(m.group(2))
        elif stack and stack[-1] == m.group(2):
            stack.pop()
    return stack


def assemble_document(body: str, preamble: str) -> str:
    """Wrap body content in the given preamble and document environment."""
    return preamble + "\n" + body + "\n\\end{document}\n"


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

_PREAMBLE_EXACT = frozenset({r"\begin{document}", r"\end{document}"})


def strip_preamble_from_body(latex: str) -> str:
    """Strip preamble lines that the model mistakenly includes in body-only output."""
    filtered = []
    for line in latex.splitlines():
        stripped = line.strip()
        if stripped.startswith(_PREAMBLE_PREFIXES) or stripped in _PREAMBLE_EXACT:
            continue
        filtered.append(line)
    return "\n".join(filtered)
