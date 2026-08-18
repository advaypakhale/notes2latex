"""FastAPI application — web UI backend."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

from notes2latex import __version__
from notes2latex.api.v1 import router as v1_router
from notes2latex.db.migrate import upgrade_to_head
from notes2latex.services import jobs

# Resolved against the working directory, which is the project root both for
# `notes2latex serve` and for the Docker image.
_FRONTEND_DIST = Path("frontend/dist")
_INDEX_HTML = _FRONTEND_DIST / "index.html"


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    await upgrade_to_head()
    await jobs.recover_interrupted()
    yield


app = FastAPI(title="notes2latex", version=__version__, lifespan=lifespan)
app.include_router(v1_router)

if _INDEX_HTML.is_file():

    @app.get("/{path:path}", include_in_schema=False)
    def frontend(path: str) -> FileResponse:
        """Serve a built asset, or the SPA shell so client-side routes survive a refresh."""
        # An unmatched API path is a mistake, not a client-side route.
        if path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not found")

        asset = (_FRONTEND_DIST / path).resolve()
        if path and asset.is_file() and asset.is_relative_to(_FRONTEND_DIST.resolve()):
            return FileResponse(asset)
        return FileResponse(_INDEX_HTML)
