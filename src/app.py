"""FastAPI application — web UI backend."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from api.v1.agent.routes import preamble_router, router as agent_router
from db.engine import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="notes2latex",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(agent_router, prefix="/api/v1")
app.include_router(preamble_router, prefix="/api/v1")

# Serve frontend static files if built.
# Resolved relative to cwd — both local dev (`uv run notes2latex serve` from project root)
# and Docker (WORKDIR /app) run from the directory containing frontend/dist.
_frontend_dist = Path("frontend/dist")
if _frontend_dist.is_dir():
    _index_html = _frontend_dist / "index.html"

    # Serve static assets (JS, CSS, images) at /assets
    app.mount("/assets", StaticFiles(directory=str(_frontend_dist / "assets")), name="assets")

    # SPA catch-all: serve index.html for any non-API route so client-side
    # routing (e.g. /settings, /jobs/abc) works on page load and refresh.
    @app.get("/{path:path}")
    async def spa_fallback(path: str):
        # Serve known static files directly (favicon, etc.)
        static_file = _frontend_dist / path
        if path and static_file.is_file() and static_file.is_relative_to(_frontend_dist):
            return FileResponse(static_file)
        return FileResponse(_index_html)
