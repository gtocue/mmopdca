# -*- coding: utf-8 -*-
"""Create commands table

Revision ID: 0001_create_commands_table
Revises: 7e0758401a54
Create Date: 2025-05-XX YY:ZZ
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision      = "0001_create_commands_table"
down_revision = "7e0758401a54"
branch_labels = None
depends_on    = None


def upgrade() -> None:
    """Create table if it does not already exist."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("commands"):
        # ensure pgcrypto extension is available
        op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

        op.create_table(
            "commands",
            sa.Column(
                "id", postgresql.UUID(as_uuid=True),
                primary_key=True,
                server_default=sa.text("gen_random_uuid()"),
            ),
            sa.Column("plan_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("do_id", postgresql.UUID(as_uuid=True)),
            sa.Column("status", sa.String(32), nullable=False),
            sa.Column(
                "created_at", sa.DateTime(timezone=True),
                nullable=False, server_default=sa.text("now()"),
            ),
            sa.Column(
                "updated_at", sa.DateTime(timezone=True),
                nullable=False, server_default=sa.text("now()"),
            ),
        )


def downgrade() -> None:
    """Drop table if it exists."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("commands"):
        op.drop_table("commands")
        op.execute("DROP EXTENSION IF EXISTS pgcrypto")
