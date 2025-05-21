"""Create commands table

Revision ID: 0001_create_commands_table
Revises: None
Create Date: 2025-05-20 21:28
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# ──────────────────── リビジョン ID ────────────────────
revision = "0001_create_commands_table"
down_revision = None
branch_labels = None
depends_on = None
# ────────────────────────────────────────────────────────


def upgrade() -> None:
    """DDL を適用（forward）"""
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
    """DDL をロールバック（backward）"""
    op.drop_table("commands")
