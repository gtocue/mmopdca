"""drop stock master tables

Revision ID: 11b979e6aa33
Revises: 0001_create_commands_table
Create Date: 2025-05-23 19:32:04.999447
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "11b979e6aa33"
down_revision: Union[str, None] = "0001_create_commands_table"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Drop legacy stock-master tables."""
    for tbl in (
        "stock_list_staging",
        "stock_list_hist",
        "stock_list",
    ):
        op.drop_table(tbl, schema="instruments")  # ← instruments スキーマ指定
    # op.drop_schema("instruments")  # スキーマ自体を捨てたいならコメントアウト解除


def downgrade() -> None:
    """Re-create tables (minimum columns) for rollback."""
    metadata = sa.MetaData(schema="instruments")

    sa.Table(
        "stock_list",
        metadata,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("symbol", sa.String(16), nullable=False, unique=True),
    )
    sa.Table(
        "stock_list_hist",
        metadata,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("symbol", sa.String(16), nullable=False),
        sa.Column("date", sa.Date, nullable=False),
    )
    sa.Table(
        "stock_list_staging",
        metadata,
        sa.Column("id", sa.Integer, primary_key=True),
    )
    metadata.create_all(op.get_bind())
