# =========================================================
# ASSIST_KEY: core/repository/postgres_impl.py
# =========================================================
#
# PostgreSQL 汎用 JSONB ストア（tenant_id, id, data, created_at）
# ---------------------------------------------------------------

from __future__ import annotations

import json
import os
from typing import Any, Dict, List

try:
    import psycopg                        # <-- ★ optional import
    from psycopg.rows import dict_row
except ModuleNotFoundError:               # psycopg 未インストールなら…
    psycopg = None                        # 型は捨ててダミー化
    dict_row = None                       # Repository を使わなければ問題なし

from .base import BaseRepository

# ------------------------------------------------------------------
# connection helper
# ------------------------------------------------------------------
_CX = None


def _connect():
    if psycopg is None:                   # <-- ★ ここで検知してエラー
        raise RuntimeError(
            "psycopg がありません。PostgreSQL を使うには "
            "`poetry install --with db` で依存を入れてください。"
        )

    dsn = os.getenv("PG_DSN")
    if dsn:
        return psycopg.connect(dsn, autocommit=True)

    return psycopg.connect(
        host=os.getenv("PG_HOST", "localhost"),
        port=int(os.getenv("PG_PORT", 5432)),
        user=os.getenv("PG_USER", "postgres"),
        password=os.getenv("PG_PASSWORD", ""),
        dbname=os.getenv("PG_DB", "mmopdca"),
        autocommit=True,
    )


def _cx():
    global _CX
    if _CX is None or _CX.closed:
        _CX = _connect()
    return _CX


# ------------------------------------------------------------------
# Repository
# ------------------------------------------------------------------
class PostgresRepository(BaseRepository):
    """
    Optional な PostgreSQL 用 Repository。
    psycopg が無い環境でインスタンス化すると RuntimeError を投げる。
    """

    def __init__(self, table: str, schema: str = "public") -> None:
        if psycopg is None:
            raise RuntimeError(
                "psycopg がインストールされていません。"
                " `poetry install --with db` を実行するか "
                "DB_BACKEND を memory / sqlite にして下さい。"
            )

        self.schema = schema
        self.table = table

        ddl = f"""
        CREATE SCHEMA IF NOT EXISTS "{schema}";
        CREATE TABLE IF NOT EXISTS "{schema}"."{table}" (
            id         TEXT PRIMARY KEY,
            data       JSONB NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        ALTER TABLE "{schema}"."{table}"
            ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ
            NOT NULL DEFAULT now();
        """
        with _cx().cursor() as cur:
            cur.execute(ddl)
            
    # ------------------------------------------------------------------ #
    # CRUD
    # ------------------------------------------------------------------ #
    def create(self, obj_id: str, data: Dict[str, Any]) -> None:
        sql = (
            f'INSERT INTO "{self.schema}"."{self.table}" '
            "(tenant_id, id, data) VALUES (%s, %s, %s) "
            "ON CONFLICT (tenant_id, id) DO UPDATE SET data = EXCLUDED.data"
        )
        with _cx().cursor() as cur:
            cur.execute(sql, (self.tenant_id, obj_id, json.dumps(data)))

    def get(self, obj_id: str) -> Dict[str, Any] | None:
        sql = (
            f'SELECT data FROM "{self.schema}"."{self.table}" '
            "WHERE tenant_id = %s AND id = %s"
        )
        with _cx().cursor(row_factory=dict_row) as cur:
            cur.execute(sql, (self.tenant_id, obj_id))
            row = cur.fetchone()
        return row["data"] if row else None

    def list(self) -> List[Dict[str, Any]]:
        sql = (
            f'SELECT data FROM "{self.schema}"."{self.table}" '
            "WHERE tenant_id = %s "
            "ORDER BY created_at DESC"
        )
        with _cx().cursor(row_factory=dict_row) as cur:
            cur.execute(sql, (self.tenant_id,))
            return [r["data"] for r in cur.fetchall()]

    def delete(self, obj_id: str) -> None:
        sql = (
            f'DELETE FROM "{self.schema}"."{self.table}" '
            "WHERE tenant_id = %s AND id = %s"
        )
        with _cx().cursor() as cur:
            cur.execute(sql, (self.tenant_id, obj_id))
