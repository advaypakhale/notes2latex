"""FastAPI application — web UI backend."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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
    app.mount("/", StaticFiles(directory=str(_frontend_dist), html=True), name="frontend")
