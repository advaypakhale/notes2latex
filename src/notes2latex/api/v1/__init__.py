"""Version 1 of the HTTP API."""

from fastapi import APIRouter

from notes2latex.api.v1 import jobs, preamble

router = APIRouter(prefix="/api/v1")
router.include_router(jobs.router)
router.include_router(preamble.router)
