"""Page markers that let a single .tex file be split back into per-page sources."""

import re

_MARKER_TEMPLATE = "% ====== Page {} ======"
_MARKER_RE = re.compile(r"^% ====== Page (\d+) ======$", re.MULTILINE)


def append_page(page_number: int, latex: str, base_body: str) -> str:
    page_content = f"{_MARKER_TEMPLATE.format(page_number)}\n{latex}"
    return f"{base_body}\n\n{page_content}" if base_body else page_content


def page_line_offset(tex_source: str, page_number: int) -> int:
    """Return how many lines of the source precede the given page's content.

    Compile errors carry line numbers for the whole document; subtracting this offset
    rebases one onto the page it belongs to. Raises LookupError if the page has no marker.
    """
    starts = [m.start() for m in _MARKER_RE.finditer(tex_source) if int(m.group(1)) == page_number]
    if not starts:
        msg = f"No marker for page {page_number}"
        raise LookupError(msg)
    # A transcription is prompted with earlier pages as context and can echo a marker back
    # into its output. The one append_page wrote is always the last.
    return tex_source.count("\n", 0, starts[-1]) + 1


def page_numbers(tex_source: str) -> set[int]:
    """Return the page numbers a .tex source has markers for."""
    return {int(match.group(1)) for match in _MARKER_RE.finditer(tex_source)}


def split_by_page(tex_source: str) -> dict[int, str]:
    """Split a .tex source into its marked pages, keyed by 1-based page number."""
    body_end = tex_source.find(r"\end{document}")
    if body_end == -1:
        body_end = len(tex_source)

    markers = list(_MARKER_RE.finditer(tex_source))
    return {
        int(match.group(1)): tex_source[
            match.end() : markers[i + 1].start() if i + 1 < len(markers) else body_end
        ].strip()
        for i, match in enumerate(markers)
    }
