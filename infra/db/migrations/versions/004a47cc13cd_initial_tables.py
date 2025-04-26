# =========================================================
# ASSIST_KEY: このファイルは【infra/db/migrations/versions/004a47cc13cd_initial_tables.py】に位置するユニットです
# =========================================================
#
# 【概要】
#   PDCA 用４テーブル(plan / do / check / act) を JSONB＋created_at 付きで作成する
#
# 【DDL 仕様】
#   id          TEXT        PRIMARY KEY
#   data        JSONB       NOT NULL
#   created_at  TIMESTAMPTZ NOT NULL  DEFAULT now()
#
#   └─ アプリは data(JSONB) に完全スキーマを保持し、RDB はメタ的に管理
#
# 【ダウングレード】
#   テーブルを DROP
#
# ---------------------------------------------------------

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# ------------------------------------------------------------------
# Alembic identifiers
# ------------------------------------------------------------------
revision: str = "004a47cc13cd"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# ------------------------------------------------------------------
# 共通カラム定義（重複排除）
# ------------------------------------------------------------------
_ID_COL = sa.Column("id", sa.Text, primary_key=True)
_DATA_COL = sa.Column("data", postgresql.JSONB(astext_type=sa.Text()), nullable=False)
_CREATED_AT_COL = sa.Column(
    "created_at",
    sa.TIMESTAMP(timezone=True),
    nullable=False,
    server_default=sa.text("now()"),
)


# ------------------------------------------------------------------
# upgrade / downgrade
# ------------------------------------------------------------------
def upgrade() -> None:
    """Create plan / do / check / act tables."""
    for tbl in ("plan", "do", "check", "act"):
        op.create_table(tbl, _ID_COL.copy(), _DATA_COL.copy(), _CREATED_AT_COL.copy())


def downgrade() -> None:
    """Drop plan / do / check / act tables."""
    for tbl in ("act", "check", "do", "plan"):  # 依存のない逆順で安全に
        op.drop_table(tbl)
