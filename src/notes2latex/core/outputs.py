"""Where a run's artifacts live on disk."""

import base64
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class JobOutputs:
    """Names every artifact of a run, so the pipeline and the API agree on where they are."""

    dir: Path

    @property
    def tex(self) -> Path:
        return self.dir / "output.tex"

    @property
    def pdf(self) -> Path:
        return self.dir / "output.pdf"

    @property
    def log(self) -> Path:
        return self.dir / "output.log"

    def page_image(self, page_number: int) -> Path:
        return self.dir / "pages" / f"page_{page_number:03d}.png"

    def write_tex(self, document: str) -> None:
        self.dir.mkdir(parents=True, exist_ok=True)
        self.tex.write_text(document, encoding="utf-8")

    def write_log(self, log_output: str) -> None:
        self.dir.mkdir(parents=True, exist_ok=True)
        self.log.write_text(log_output, encoding="utf-8")

    def save_page_images(self, pages_b64: list[str]) -> None:
        (self.dir / "pages").mkdir(parents=True, exist_ok=True)
        for page_number, data in enumerate(pages_b64, start=1):
            self.page_image(page_number).write_bytes(base64.b64decode(data))
