# =====================================================================
# core/repository/factory.py
# ---------------------------------------------------------------------
#   環境変数 DB_BACKEND で Repository 実装を切り替えるファクトリ。
#     • memory   (default)          – プロセスメモリ
#     • sqlite                       – 単一ファイル SQLite
#     • postgres  (optional)        – PostgreSQL
#     • redis     (optional)        – Redis Key-Value
# =====================================================================
from __future__ import annotations

import logging
import os

from .memory_impl import MemoryRepository
from .sqlite_impl import SQLiteRepository

logger = logging.getLogger(__name__)

# ── Optional back-ends ───────────────────────────────────
try:
    from .postgres_impl import PostgresRepository  # type: ignore

    _HAS_PG = True
except ModuleNotFoundError:
    PostgresRepository = None  # type: ignore[assignment]
    _HAS_PG = False

try:
    from .redis_impl import RedisRepository  # type: ignore

    _HAS_REDIS = True
except ModuleNotFoundError:
    RedisRepository = None  # type: ignore[assignment]
    _HAS_REDIS = False

_SUPPORTED = (
    {"memory", "sqlite"}
    | ({"postgres"} if _HAS_PG else set())
    | ({"redis"} if _HAS_REDIS else set())
)


def get_repo(table: str = "plan"):
    """
    Repository を返す（Memory / SQLite / Postgres / Redis）。

    Parameters
    ----------
    table : str
        コレクション / テーブル名
    """
    backend = os.getenv("DB_BACKEND", "memory").lower()

    # SQLite
    if backend == "sqlite":
        return SQLiteRepository(table=table)

    # PostgreSQL
    if backend == "postgres" and _HAS_PG:
        schema = os.getenv("PG_SCHEMA", "public")
        return PostgresRepository(table=table, schema=schema)  # type: ignore[call-arg]

    # Redis
    if backend == "redis" and _HAS_REDIS:
        return RedisRepository(table=table)  # ← 統一

    # フォールバック
    if backend not in _SUPPORTED:
        logger.warning(
            "[RepoFactory] unknown backend '%s' → MemoryRepository にフォールバック",
            backend,
        )
    return MemoryRepository(table=table)
