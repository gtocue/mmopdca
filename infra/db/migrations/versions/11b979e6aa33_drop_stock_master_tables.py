# -*- coding: utf-8 -*-
"""
Drop stock master tables

Revision ID: 11b979e6aa33
Revises: 0001_create_commands_table
Create Date: 2025-05-23 19:32:04.999447
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# ───────────────────────
# Alembic メタデータ
# ───────────────────────
revision: str = "11b979e6aa33"
down_revision: Union[str, None] = "0001_create_commands_table"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = "instruments"
TABLES = (
    "stock_list_staging",
    "stock_list_hist",
    "stock_list",
)

# ───────────────────────
# upgrade  : テーブル削除
# downgrade: ざっくり再作成
# ───────────────────────
def upgrade() -> None:
    """Drop legacy stock-master tables."""
    for tbl in TABLES:
        op.drop_table(tbl, schema=SCHEMA)

    # スキーマ自体も不要なら下行をアンコメント
    # op.execute(sa.text(f'DROP SCHEMA IF EXISTS "{SCHEMA}" CASCADE'))


def downgrade() -> None:
    """Re-create minimum-structure tables for rollback."""
    metadata = sa.MetaData(schema=SCHEMA)

    # インデックスや制約は最低限だけ置く
    sa.Table(
        "stock_list",
        metadata,
        sa.Column("code", sa.String(12), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
    )

    sa.Table(
        "stock_list_hist",
        metadata,
        sa.Column("code", sa.String(12), primary_key=True),
        sa.Column("as_of_date", sa.Date, primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
    )

    sa.Table(
        "stock_list_staging",
        metadata,
        sa.Column("code", sa.String(12), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("loaded_at", sa.DateTime, nullable=False),
    )

    # CREATE TABLE … を実行
    metadata.create_all(op.get_bind())
