# =========================================================
# ASSIST_KEY: このファイルは【core/repository/postgres_impl.py】に位置するユニットです
# =========================================================
#
# 概要:
#   - JSONB ストア (id, data, created_at) を提供する共通 Repository
#   - テーブルが既に存在しても created_at 列が無ければ起動時に自動追加
#   - autocommit=True でトランザクションを簡素化（MVP）
# ----------------------------------------------------------

from __future__ import annotations

import json
import os
from typing import Any, Dict, List

import psycopg
from psycopg.rows import dict_row

from .base import BaseRepository

# ---------- 接続シングルトン ----------
_CX: psycopg.Connection | None = None


def _connect() -> psycopg.Connection:
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


def _cx() -> psycopg.Connection:
    global _CX  # noqa: PLW0603
    if _CX is None or _CX.closed:
        _CX = _connect()
    return _CX


# ---------- Repository ----------
class PostgresRepository(BaseRepository):
    """
    テーブル (id TEXT PK , data JSONB , created_at TIMESTAMPTZ) を
    アプリ起動時に自動生成／補正して使う超軽量リポジトリ
    """

    def __init__(self, table: str, schema: str = "public") -> None:
        self.schema = schema
        self.table = table

        ddl = f"""
        CREATE SCHEMA IF NOT EXISTS "{schema}";
        CREATE TABLE IF NOT EXISTS "{schema}"."{table}" (
            id         TEXT  PRIMARY KEY,
            data       JSONB NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        -- 既存に created_at が無ければ追加
        ALTER TABLE "{schema}"."{table}"
            ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ
            NOT NULL DEFAULT now();
        """
        with _cx().cursor() as cur:
            cur.execute(ddl)

    # ---------- CRUD ----------
    def create(self, obj_id: str, data: Dict[str, Any]) -> None:
        sql = f'INSERT INTO "{self.schema}"."{self.table}"(id,data) VALUES (%s,%s)'
        with _cx().cursor() as cur:
            cur.execute(sql, (obj_id, json.dumps(data)))

    def get(self, obj_id: str) -> Dict[str, Any] | None:
        sql = f'SELECT data FROM "{self.schema}"."{self.table}" WHERE id=%s'
        with _cx().cursor(row_factory=dict_row) as cur:
            cur.execute(sql, (obj_id,))
            row = cur.fetchone()
        return row["data"] if row else None

    def list(self) -> List[Dict[str, Any]]:
        sql = f'SELECT data FROM "{self.schema}"."{self.table}"'
        with _cx().cursor(row_factory=dict_row) as cur:
            cur.execute(sql)
            return [r["data"] for r in cur.fetchall()]

    def delete(self, obj_id: str) -> None:
        sql = f'DELETE FROM "{self.schema}"."{self.table}" WHERE id=%s'
        with _cx().cursor() as cur:
            cur.execute(sql, (obj_id,))
