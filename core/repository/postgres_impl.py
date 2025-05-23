# =========================================================
# ASSIST_KEY: 【core/repository/postgres_impl.py】
# =========================================================
#
# PostgreSQL ― 汎用 JSONB ストア  (psycopg-3 sync)
# ---------------------------------------------------------
# • tenant_id + id を複合 PK、data を JSONB で保存
# • psycopg 未インストール環境でも import エラーにならない
# • pytest 実行時は eager=False で “遅延接続” し
#   実 DB が無くても import／生成だけは通る設計
# ---------------------------------------------------------
from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List, Optional

try:
    import psycopg  # type: ignore
    from psycopg.rows import dict_row  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    psycopg = None  # type: ignore
    dict_row = None  # type: ignore

from .base import BaseRepository

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------- #
# env helper with bytes decoding
# --------------------------------------------------------------------- #
def _get_env_var(name: str) -> str | None:
    if name in os.environ:
        return os.environ.get(name)
    environb = getattr(os, "environb", None)
    if environb:
        bname = name.encode()
        if bname in environb:
            raw = environb[bname]
            if isinstance(raw, bytes):
                try:
                    return raw.decode("utf-8")
                except UnicodeDecodeError:
                    return raw.decode("cp932", "ignore")
    return None


# --------------------------------------------------------------------- #
# DSN helper
# --------------------------------------------------------------------- #
def _env(primary: str, fallback: str, default: str = "") -> str:
    return os.getenv(primary) or os.getenv(fallback) or default


def _make_dsn() -> dict[str, Any] | str:
    if dsn := _get_env_var("PG_DSN"):
        return dsn  # 完全 DSN
    if dsn := _get_env_var("DATABASE_URL"):
        return dsn
    return dict(
        host=_env("PG_HOST", "POSTGRES_HOST", "db"),
        port=int(_env("PG_PORT", "POSTGRES_PORT", "5432")),
        dbname=_env("PG_DB", "POSTGRES_DB", "mmopdca"),
        user=_env("PG_USER", "POSTGRES_USER", "mmopdca"),
        password=_env("PG_PASSWORD", "POSTGRES_PASSWORD", "secret"),
    )


# --------------------------------------------------------------------- #
# connection singleton
# --------------------------------------------------------------------- #
_CX: Optional["psycopg.Connection[Any]"] = None


def _cx():
    global _CX
    if _CX is None or _CX.closed:
        if psycopg is None:  # psycopg 未インストール
            raise RuntimeError(
                "psycopg がインストールされていません。 "
                "DB_BACKEND を memory/sqlite/redis にするか "
                "`poetry install --with db` を実行してください。"
            )
        dsn = _make_dsn()
        if isinstance(dsn, str):
            _CX = psycopg.connect(dsn, autocommit=True)
        else:
            _CX = psycopg.connect(**dsn, autocommit=True)
         dsn = _make_dsn()
        if isinstance(dsn, str):
            _CX = psycopg.connect(dsn, autocommit=True)
        else:
            _CX = psycopg.connect(**dsn, autocommit=True)           
    return _CX


# --------------------------------------------------------------------- #
# Repository implementation
# --------------------------------------------------------------------- #
class PostgresRepository(BaseRepository):
    """
    PostgreSQL(JSONB) Repository。

    * `eager=False` にすると **DDL/接続を遅延** させられるので
      pytest で実 DB が無くても import だけは成功。
    """

    tenant_id: str = ""  # （単一テナント前提）

    def __init__(
        self,
        *,
        table: str,
        schema: str = "public",
        eager: bool = False,  # ★ デフォルトを遅延へ変更
    ) -> None:
        super().__init__(table=table)  # type: ignore[arg-type]
        self.table = table
        self.schema = schema
        self._initialized = False
        if eager:
            self._ensure_table()

    # ---------------- internal ----------------
    def _ensure_table(self) -> None:
        if self._initialized:
            return
        ddl = f"""
        CREATE SCHEMA IF NOT EXISTS "{self.schema}";
        CREATE TABLE IF NOT EXISTS "{self.schema}"."{self.table}" (
            tenant_id  TEXT        NOT NULL DEFAULT '',
            id         TEXT        NOT NULL,
            data       JSONB       NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            PRIMARY KEY (tenant_id, id)
        );
        """
        with _cx().cursor() as cur:
            cur.execute(ddl)
        self._initialized = True

    def _lazy(self) -> None:
        if not self._initialized:
            self._ensure_table()

    # ---------------- CRUD --------------------
    def create(self, obj_id: str, data: Dict[str, Any]) -> None:
        self._lazy()
        sql = (
            f'INSERT INTO "{self.schema}"."{self.table}" (tenant_id,id,data) '
            "VALUES (%s,%s,%s) "
            "ON CONFLICT (tenant_id,id) DO UPDATE SET data = EXCLUDED.data"
        )
        with _cx().cursor() as cur:
            cur.execute(sql, (self.tenant_id, obj_id, json.dumps(data)))

    update = create  # up-sert 同義

    def get(self, obj_id: str) -> Dict[str, Any] | None:
        self._lazy()
        sql = (
            f'SELECT data FROM "{self.schema}"."{self.table}" '
            "WHERE tenant_id=%s AND id=%s"
        )
        with _cx().cursor(row_factory=dict_row) as cur:  # type: ignore[arg-type]
            cur.execute(sql, (self.tenant_id, obj_id))
            row = cur.fetchone()
        return row["data"] if row else None

    def delete(self, obj_id: str) -> None:
        self._lazy()
        sql = (
            f'DELETE FROM "{self.schema}"."{self.table}" '
            "WHERE tenant_id=%s AND id=%s"
        )
        with _cx().cursor() as cur:
            cur.execute(sql, (self.tenant_id, obj_id))

    def list(self) -> List[Dict[str, Any]]:
        self._lazy()
        sql = (
            f'SELECT data FROM "{self.schema}"."{self.table}" '
            "WHERE tenant_id=%s ORDER BY created_at DESC"
        )
        with _cx().cursor(row_factory=dict_row) as cur:  # type: ignore[arg-type]
            cur.execute(sql, (self.tenant_id,))
            return [r["data"] for r in cur.fetchall()]
