# =========================================================
# ASSIST_KEY: infra/db/migrations/versions/44d6ab02d62f_created_at_not_null.py
# =========================================================
"""created_at 列を NOT NULL にする

Revision ID: 44d6ab02d62f
Revises: 004a47cc13cd
Create Date: 2025-04-26 20:35:00
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# ──────────────────────────────────────────────
revision: str = "44d6ab02d62f"
down_revision: Union[str, None] = "004a47cc13cd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None
# ──────────────────────────────────────────────


def _ensure_created_at(table: str) -> None:
    """IF NOT EXISTS で列を追加 → 値を埋めて → NOT NULL 制約を付ける"""
    # 1) 追加（無ければ）
    op.execute(
        f'ALTER TABLE "{table}" '
        f'ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT now();'
    )
    # 2) NULL 行を埋める（途中で列を作った場合に備える）
    op.execute(f'UPDATE "{table}" SET created_at = now() WHERE created_at IS NULL;')
    # 3) NOT NULL 制約
    op.execute(f'ALTER TABLE "{table}" ALTER COLUMN created_at SET NOT NULL;')


def upgrade() -> None:
    """Upgrade schema."""
    for tbl in ("plan", "do", "check", "act"):
        _ensure_created_at(tbl)


def downgrade() -> None:
    """Downgrade schema (drop created_at)."""
    for tbl in ("plan", "do", "check", "act"):
        op.execute(f'ALTER TABLE "{tbl}" DROP COLUMN IF EXISTS created_at;')
