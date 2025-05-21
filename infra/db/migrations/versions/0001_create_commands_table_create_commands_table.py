"""Create commands table

Revision ID: 0001_create_commands_table
Revises:      None
Create Date:  2025-05-20 21:28
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_create_commands_table"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "commands",
        sa.Column("id",           postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("plan_id",      postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("do_id",        postgresql.UUID(as_uuid=True)),
        sa.Column("status",       sa.String(32), nullable=False),
        sa.Column("created_at",   sa.TIMESTAMP(timezone=True),
                                  server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at",   sa.TIMESTAMP(timezone=True),
                                  server_default=sa.text("now()"), nullable=False),
    )
    # ID はアプリ側で uuid.uuid4() を渡す運用にして
    # サーバーサイドの gen_random_uuid() 依存をなくしています


def downgrade() -> None:
    op.drop_table("commands")
