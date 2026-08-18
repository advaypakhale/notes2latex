"""Alembic environment.

The caller opens the connection and passes it in `config.attributes`, because the app runs
migrations against its own async engine at startup.
"""

from alembic import context
from sqlalchemy import Connection
from sqlmodel import SQLModel

from notes2latex.db import models  # noqa: F401 — registers the tables on SQLModel.metadata

connection: Connection = context.config.attributes["connection"]

context.configure(
    connection=connection,
    target_metadata=SQLModel.metadata,
    # SQLite can only ALTER TABLE in narrow cases; batch mode rebuilds the table instead.
    render_as_batch=True,
)

with context.begin_transaction():
    context.run_migrations()
