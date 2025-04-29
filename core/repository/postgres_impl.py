# =========================================================
# core/repository/postgres_impl.py
# =========================================================
#
# PostgreSQL 汎用 JSONB ストア
# ---------------------------------------------------------
# * tenant_id + id を複合 PK とし、data を丸ごと JSONB で保存
# * memory / sqlite / postgres を動的に切り替える factory から
#   呼び出される **PostgreSQL 専用** Repository 実装
#
# 依存
# ----
#   pip install "psycopg[binary]"  (psycopg-3 sync 版)
#
# 環境変数の優先順位
# ------------------
#   1. PG_DSN                              … 完全 DSN
#   2. PG_* / POSTGRES_*                   … 個別指定
#      (PG_* が無ければ POSTGRES_* を見る)
#   3. compose 用デフォルト
# =========================================================
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------
# optional import ― DB を使わない構成でも import error にしない
# ---------------------------------------------------------
try:
    import psycopg                         # psycopg-3 (sync)
    from psycopg.rows import dict_row
except ModuleNotFoundError:                # noqa: D401
    psycopg = None                         # 型ヒントはダミー化
    dict_row = None

from .base import BaseRepository

# ---------------------------------------------------------
# connection helper
# ---------------------------------------------------------
_CX: Optional["psycopg.Connection[Any]"] = None


def _env(primary: str, fallback: str, default: str = "") -> str:
    """`PG_* → POSTGRES_* → default` の順で環境変数を解決"""
    return os.getenv(primary) or os.getenv(fallback) or default


def _connect():
    """環境変数を解釈し、シングルトン接続を生成／取得する"""
    if psycopg is None:  # psycopg が import 出来なかった
        raise RuntimeError(
            "psycopg がインストールされていません。\n"
            "  • DB_BACKEND を memory / sqlite に変更するか\n"
            "  • `poetry install --with db` を実行してください。"
        )

    # 完全 DSN が与えられている場合
    if dsn := os.getenv("PG_DSN"):
        return psycopg.connect(dsn, autocommit=True)

    # compose 用デフォルト
    return psycopg.connect(
        host=_env("PG_HOST", "POSTGRES_HOST", "db"),
        port=int(_env("PG_PORT", "POSTGRES_PORT", "5432")),
        dbname=_env("PG_DB", "POSTGRES_DB", "mmopdca"),
        user=_env("PG_USER", "POSTGRES_USER", "mmop_user"),
        password=_env("PG_PASSWORD", "POSTGRES_PASSWORD", "secret"),
        autocommit=True,
    )


def _cx():
    """lazy singleton connection"""
    global _CX
    if _CX is None or _CX.closed:
        _CX = _connect()
    return _CX


# ---------------------------------------------------------
# Repository implementation
# ---------------------------------------------------------
class PostgresRepository(BaseRepository):
    """
    PostgreSQL(JSONB) 実装。

    * psycopg が import できない場合 → RuntimeError
    * <schema>.<table> が無ければ自動生成（CREATE SCHEMA/TABLE）
    """

    def __init__(self, *, table: str, schema: str = "public") -> None:
        if psycopg is None:
            raise RuntimeError(
                "psycopg がインストールされていません。\n"
                "  • DB_BACKEND を memory / sqlite に変更するか\n"
                "  • `poetry install --with db` を実行してください。"
            )

        # BaseRepository へ table / tenant_id を渡す
        super().__init__(table=table)      # tenant_id はデフォルト '' のまま

        self.schema: str = schema
        self.table: str = table

        # ---------- 初回 DDL ----------
        ddl = f"""
        CREATE SCHEMA IF NOT EXISTS "{schema}";

        CREATE TABLE IF NOT EXISTS "{schema}"."{table}" (
            tenant_id  TEXT      NOT NULL DEFAULT '',
            id         TEXT      NOT NULL,
            data       JSONB     NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            PRIMARY KEY (tenant_id, id)
        );
        """
        with _cx().cursor() as cur:
            cur.execute(ddl)

    # -----------------------------------------------------
    # CRUD
    # -----------------------------------------------------
    def create(self, obj_id: str, data: Dict[str, Any]) -> None:
        sql = (
            f'INSERT INTO "{self.schema}"."{self.table}" '
            "(tenant_id, id, data) VALUES (%s, %s, %s) "
            "ON CONFLICT (tenant_id, id) DO UPDATE "
            "   SET data = EXCLUDED.data"
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
