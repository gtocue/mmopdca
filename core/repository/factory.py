# =====================================================================
# core/repository/factory.py
# ---------------------------------------------------------------------
# Repository 実装ファクトリ
#
#   環境変数 `DB_BACKEND` で下記いずれかを選択する。
#       • memory   … プロセスメモリ (デフォルト／テスト向け)
#       • sqlite   … 単一ファイル SQLite
#       • postgres … PostgreSQL  (← NEW / optional)
#
#   ※ postgres 用ドライバ / 実装モジュールが import 出来なければ
#     自動的に memory にフォールバックする。
# =====================================================================
from __future__ import annotations

import os
import logging

from .memory_impl import MemoryRepository
from .sqlite_impl import SQLiteRepository

logger = logging.getLogger(__name__)

# ------------------------------------------------------------
# オプション: PostgreSQL 実装は存在すれば import
# ------------------------------------------------------------
try:
    from .postgres_impl import PostgresRepository  # type: ignore
    _HAS_PG = True
except ModuleNotFoundError:  # pragma: no cover
    _HAS_PG = False
    PostgresRepository = None  # type: ignore[assignment]

_SUPPORTED = {"memory", "sqlite"} | ({"postgres"} if _HAS_PG else set())


# ------------------------------------------------------------
# Public factory
# ------------------------------------------------------------
def get_repo(table: str = "plan"):
    """
    使用する Repository を返す。

    Parameters
    ----------
    table : str
        テーブル（コレクション）名。実装により意味は多少異なる。

    Returns
    -------
    BaseRepository
        MemoryRepository / SQLiteRepository / PostgresRepository のいずれか
    """
    backend = os.getenv("DB_BACKEND", "memory").lower()

    if backend == "sqlite":
        return SQLiteRepository(table=table)

    if backend == "postgres":
        if _HAS_PG:
            return PostgresRepository(  # type: ignore[call-arg]
                table=table,
                schema=os.getenv("PG_SCHEMA", "public"),
            )
        logger.warning(
            "[RepoFactory] postgres_impl が無いため MemoryRepository にフォールバックします"
        )

    # デフォルト（または fallback）
    return MemoryRepository(table=table)
