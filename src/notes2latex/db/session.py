"""Async SQLite engine and session handling."""

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

from notes2latex.core.config import get_settings

DB_PATH = get_settings().data_dir / "notes2latex.db"

engine = create_async_engine(f"sqlite+aiosqlite:///{DB_PATH}")


async def get_session() -> AsyncIterator[AsyncSession]:
    async with AsyncSession(engine) as session:
        yield session
