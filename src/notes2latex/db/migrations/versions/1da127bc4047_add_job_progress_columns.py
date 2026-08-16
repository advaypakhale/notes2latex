"""add job progress columns

Revision ID: 1da127bc4047
Revises: d239466fbb2a
Create Date: 2026-08-16 07:07:01.079823

"""

import sqlalchemy as sa
from alembic import op

revision: str = "1da127bc4047"
down_revision: str | None = "d239466fbb2a"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    with op.batch_alter_table("job") as batch_op:
        batch_op.add_column(
            sa.Column(
                "phase",
                sa.Enum("TRANSCRIBING", "COMPILING", "FIXING", "FINALIZING", name="jobphase"),
                nullable=True,
            )
        )
        # server_default fills the column for rows that already exist.
        batch_op.add_column(
            sa.Column("current_page", sa.Integer(), nullable=False, server_default="0")
        )


def downgrade() -> None:
    with op.batch_alter_table("job") as batch_op:
        batch_op.drop_column("current_page")
        batch_op.drop_column("phase")
