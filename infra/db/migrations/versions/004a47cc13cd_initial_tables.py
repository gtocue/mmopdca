# =========================================================
# ASSIST_KEY: infra/db/migrations/versions/004a47cc13cd_initial_tables.py
# =========================================================
#
# 汎用オートメーション・オーケストレータ ─ “初期 4 テーブル” 定義
#
#   tenant_id   TEXT        NOT NULL  DEFAULT 'public'
#   id          TEXT        NOT NULL
#   data        JSONB       NOT NULL
#   created_at  TIMESTAMPTZ NOT NULL  DEFAULT now()
#
#   PRIMARY KEY (tenant_id, id)
#   INDEX       (tenant_id, created_at DESC)
#
# ---------------------------------------------------------------------------

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# ---------------------------------------------------------------------------
# Alembic identifiers
# ---------------------------------------------------------------------------
revision: str = "004a47cc13cd"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# ---------------------------------------------------------------------------
# 共通カラム
# ---------------------------------------------------------------------------
_TENANT_COL = sa.Column(
    "tenant_id",
    sa.Text,
    nullable=False,
    server_default=sa.text("'public'"),
)
_ID_COL = sa.Column("id", sa.Text, nullable=False)
_DATA_COL = sa.Column(
    "data",
    postgresql.JSONB(astext_type=sa.Text()),
    nullable=False,
)
_CREATED_AT_COL = sa.Column(
    "created_at",
    sa.TIMESTAMP(timezone=True),
    nullable=False,
    server_default=sa.text("now()"),
)

# ---------------------------------------------------------------------------
# upgrade / downgrade
# ---------------------------------------------------------------------------
_TABLES = ("plan", "do", "check", "act")


def upgrade() -> None:
    """Create plan / do / check / act tables with tenant isolation."""
    for tbl in _TABLES:
        op.create_table(
            tbl,
            _TENANT_COL.copy(),
            _ID_COL.copy(),
            _DATA_COL.copy(),
            _CREATED_AT_COL.copy(),
            sa.PrimaryKeyConstraint("tenant_id", "id", name=f"{tbl}_pkey"),
        )
        # created_at 降順でクエリする用インデックス
        op.create_index(
            f"idx_{tbl}__tenant_created_at",
            tbl,
            ["tenant_id", sa.text("created_at DESC")],
        )


def downgrade() -> None:
    """Drop plan / do / check / act tables (indexes drop cascade)."""
    for tbl in reversed(_TABLES):  # 依存なし逆順
        op.drop_index(f"idx_{tbl}__tenant_created_at", table_name=tbl)
        op.drop_table(tbl)
