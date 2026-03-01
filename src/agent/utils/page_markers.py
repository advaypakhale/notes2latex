"""Shared helpers for page marker formatting used by graph nodes and API routes."""

import re

PAGE_MARKER_TEMPLATE = "% ====== Page {} ======"
PAGE_MARKER_RE = re.compile(r"^% ====== Page (\d+) ======$", re.MULTILINE)


def format_page_marker(page_number: int) -> str:
    """Return the page marker comment line for a 1-based page number."""
    return PAGE_MARKER_TEMPLATE.format(page_number)


def prepend_page_marker(page_number: int, latex: str, base_body: str) -> str:
    """Wrap *latex* with a page marker and append to *base_body*.

    Returns the new accumulated body string.
    """
    page_content = f"{format_page_marker(page_number)}\n{latex}"
    if base_body:
        return f"{base_body}\n\n{page_content}"
    return page_content
