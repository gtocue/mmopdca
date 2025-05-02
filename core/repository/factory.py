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

# ───────── Optional: PostgreSQL ─────────
try:
    from .postgres_impl import PostgresRepository  # type: ignore
    _HAS_PG = True
except ModuleNotFoundError:                        # pragma: no cover
    PostgresRepository = None                      # type: ignore[assignment]
    _HAS_PG = False

# ───────── Optional: Redis ──────────────
try:
    from .redis_impl import RedisRepository        # type: ignore
    _HAS_REDIS = True
except ModuleNotFoundError:                        # pragma: no cover
    RedisRepository = None                         # type: ignore[assignment]
    _HAS_REDIS = False

_SUPPORTED = {"memory", "sqlite"} | (
    {"postgres"} if _HAS_PG else set()
) | ({"redis"} if _HAS_REDIS else set())


def get_repo(table: str = "plan"):
    """
    Repository インスタンスを返す。

    Parameters
    ----------
    table : str
        コレクション / テーブル名（Memory・SQL 系実装のみ使用）
    """
    backend = os.getenv("DB_BACKEND", "memory").lower()

    # ---- SQLite ----------------------------------------------------
    if backend == "sqlite":
        return SQLiteRepository(table=table)

    # ---- PostgreSQL -----------------------------------------------
    if backend == "postgres" and _HAS_PG:
        schema = os.getenv("PG_SCHEMA", "public")
        return PostgresRepository(table=table, schema=schema)  # type: ignore[call-arg]

    # ---- Redis -----------------------------------------------------
    if backend == "redis" and _HAS_REDIS:
        # RedisRepository(key_prefix=...) というシグネチャを想定
        return RedisRepository(key_prefix=table)               # type: ignore[call-arg]

    # ---- フォールバック -------------------------------------------
    if backend not in _SUPPORTED:
        logger.warning(
            "[RepoFactory] unknown backend '%s' → MemoryRepository へフォールバック",
            backend,
        )
    return MemoryRepository(table=table)