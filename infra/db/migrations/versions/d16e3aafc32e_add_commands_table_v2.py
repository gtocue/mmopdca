"""Add commands table v2

Revision ID: d16e3aafc32e
Revises: 0001_create_commands_table
Create Date: 2025-05-XX YY:ZZ
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# ────────────────────────────────────────────────
revision      = "d16e3aafc32e"
down_revision = "0001_create_commands_table"   # ← ここを必ず 0001 に
branch_labels = None
depends_on    = None
# ────────────────────────────────────────────────


def upgrade() -> None:
    """DDL (forward)"""
    op.create_table(
        "commands",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("plan_id",  postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("do_id",    postgresql.UUID(as_uuid=True)),
        sa.Column("status",   sa.String(32),  nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )


def downgrade() -> None:
    """DDL (rollback)"""
    op.drop_table("commands")
