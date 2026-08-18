"""Turn input PDFs and images into page images the vision model can read."""

import base64
from io import BytesIO
from pathlib import Path

import pymupdf
from PIL import Image

IMAGE_SUFFIXES = frozenset({".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp"})


def load_pages(
    file_paths: list[Path], dpi: int = 300, max_page_pixels: int = 60_000_000
) -> list[str]:
    """Render the given files to a page-ordered list of base64 PNGs.

    Raises ValueError for an unsupported file extension, or for a page that would render
    to more than ``max_page_pixels`` pixels.
    """
    pages: list[str] = []
    for file_path in file_paths:
        suffix = file_path.suffix.lower()
        if suffix == ".pdf":
            pages.extend(_pdf_to_base64_pages(file_path, dpi, max_page_pixels))
        elif suffix in IMAGE_SUFFIXES:
            with Image.open(file_path) as img:
                _check_page_size(img.width, img.height, max_page_pixels, file_path.name)
                pages.append(_pil_to_base64(img.convert("RGB")))
        else:
            msg = f"Unsupported file type: {suffix}"
            raise ValueError(msg)
    return pages


def _check_page_size(width: int, height: int, max_page_pixels: int, source: str) -> None:
    if width * height > max_page_pixels:
        msg = f"{source} is {width}x{height} pixels, above the {max_page_pixels} pixel limit"
        raise ValueError(msg)


def _pdf_to_base64_pages(pdf_path: Path, dpi: int, max_page_pixels: int) -> list[str]:
    pages: list[str] = []
    scale = dpi / 72.0
    matrix = pymupdf.Matrix(scale, scale)
    with pymupdf.open(str(pdf_path)) as doc:
        for number, page in enumerate(doc, start=1):
            # A PDF can declare a page size of any dimensions, so this is checked against the
            # declared box rather than after get_pixmap has tried to allocate the buffer.
            _check_page_size(
                round(page.rect.width * scale),
                round(page.rect.height * scale),
                max_page_pixels,
                f"{pdf_path.name} page {number} at {dpi} DPI",
            )
            pix = page.get_pixmap(matrix=matrix)
            pages.append(
                _pil_to_base64(Image.frombytes("RGB", [pix.width, pix.height], pix.samples))
            )
    return pages


def _pil_to_base64(img: Image.Image) -> str:
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")
