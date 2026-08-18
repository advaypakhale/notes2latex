"""Bringing the database schema up to date."""

from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import Connection, inspect

from notes2latex.db.session import DB_PATH, engine

_MIGRATIONS_DIR = Path(__file__).parent / "migrations"

# A database with a job table but no recorded revision already has this revision's schema,
# so it is stamped rather than upgraded from empty.
_UNSTAMPED_REVISION = "d239466fbb2a"


class MigrationError(RuntimeError):
    """A failed migration. Its message is written for whoever started the server."""


async def upgrade_to_head() -> None:
    """Create or upgrade the database, raising MigrationError if it cannot be brought up to date."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    try:
        async with engine.begin() as conn:
            await conn.run_sync(_upgrade)
    except Exception as exc:
        msg = (
            f"notes2latex: could not upgrade the database at {DB_PATH}.\n"
            "\n"
            f"  {exc}\n"
            "\n"
            "The server does not start until that file is at the current schema. Restore\n"
            "it from a backup, or move it aside to start from an empty one, then restart."
        )
        raise MigrationError(msg) from exc
    finally:
        # The connection this leaves pooled belongs to the loop that ran the migration,
        # which is not always the loop that goes on to serve requests.
        await engine.dispose()


def _upgrade(connection: Connection) -> None:
    config = Config()
    config.set_main_option("script_location", str(_MIGRATIONS_DIR))
    config.attributes["connection"] = connection

    revision = MigrationContext.configure(connection).get_current_revision()
    if revision is None and "job" in set(inspect(connection).get_table_names()):
        command.stamp(config, _UNSTAMPED_REVISION)

    command.upgrade(config, "head")
