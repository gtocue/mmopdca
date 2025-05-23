"""drop stock master tables

Revision ID: 11b979e6aa33
Revises: 0001_create_commands_table
Create Date: 2025-05-23 19:32:04.999447
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "11b979e6aa33"
down_revision: Union[str, None] = "0001_create_commands_table"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# --- 対象スキーマとテーブル名をまとめておくと保守が楽 ---
SCHEMA = "instruments"
TABLES = [
    "stock_list",
    "stock_list_hist",
    "stock_list_staging",
]


def upgrade() -> None:
    """DROP 3 stock-master tables."""
    for tbl in TABLES:
        op.drop_table(tbl, schema=SCHEMA)


def downgrade() -> None:
    """最小構成の stub を再作成（巻き戻し用）"""
    # 通常は downgrade しない想定だが、CI テスト等で必要になる
    for tbl in TABLES:
        op.create_table(
            tbl,
            sa.Column("id", sa.BigInteger, primary_key=True),
            schema=SCHEMA,
        )
