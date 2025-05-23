# =========================================================
# ASSIST_KEY: このファイルは【infra/db/migrations/versions/7e0758401a54_add_index_on_created_at.py】に位置するユニットです
# =========================================================
#
# 【概要】
#   既存 5 テーブル（plan / do / check / act / commands）に
#   `created_at` 用の降順インデックスを追加するマイグレーション。
#
# 【注意】
#   - IF NOT EXISTS を付けているので **何度流しても安全**。
#   - SQLite では DESC が無視されるがエラーにならないため共通 SQL で実行。
#   - Downgrade では DROP INDEX IF EXISTS で巻き戻し可能。
#
# ---------------------------------------------------------

"""add index on created_at

Revision ID: 7e0758401a54
Revises: 44d6ab02d62f
Create Date: 2025-04-26 21:24:08.470235
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op

# ──────────────────────────────────────────────────────────
# Alembic メタデータ
# ──────────────────────────────────────────────────────────
revision: str = "7e0758401a54"
down_revision: Union[str, None] = "44d6ab02d62f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# 対象テーブル
_TABLES = ("plan", "do", "check", "act", "commands")


# ──────────────────────────────────────────────────────────
# upgrade / downgrade
# ──────────────────────────────────────────────────────────
def upgrade() -> None:  # noqa: D401
    """Apply index additions."""
    for tbl in _TABLES:
        op.execute(
            f"CREATE INDEX IF NOT EXISTS idx_{tbl}__created_at "
            f'ON "{tbl}" (created_at DESC);'
        )


def downgrade() -> None:  # noqa: D401
    """Revert index additions."""
    for tbl in _TABLES:
        op.execute(f"DROP INDEX IF EXISTS idx_{tbl}__created_at;")
