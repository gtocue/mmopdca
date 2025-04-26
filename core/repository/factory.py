# =========================================================
# ASSIST_KEY: このファイルは【core/repository/factory.py】に位置するユニットです
# =========================================================
#
# 【概要】
#   Repository 実装（memory / sqlite …）を環境変数で切り替える
#   シンプルなファクトリー。
#
# ---------------------------------------------------------

from __future__ import annotations

import os

from .memory_impl import MemoryRepository  
from .sqlite_impl import SQLiteRepository  
from .postgres_impl import PostgresRepository      # ★追加

_SUPPORTED = {"memory", "sqlite"}


def get_repo(table: str = "plan"):
    """
    `DB_BACKEND` 環境変数（memory / sqlite）で実装を切り替える。

    Parameters
    ----------
    table : str
        使用するテーブル名（プラン用・チェック用など）

    Returns
    -------
    BaseRepository
    """
    backend = os.getenv("DB_BACKEND", "memory").lower()
    if backend == "sqlite":
        return SQLiteRepository(table=table)
    if backend == "postgres":
        return PostgresRepository(table=table, schema=os.getenv("PG_SCHEMA", "public"))
    return MemoryRepository(table=table)
