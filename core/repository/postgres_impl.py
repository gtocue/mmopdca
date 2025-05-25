# =====================================================================
# core/repository/postgres_impl.py
# ---------------------------------------------------------------------
#  psycopg-3 同期ドライバで実装する JSONB 汎用ストア
#  • tenant_id + id を複合 PK に
#  • eager=False なら pytest で DB が無くても import が通る
# =====================================================================

from __future__ import annotations

import json
import logging
import os
from typing import (
    Any,
    Dict,
    List,
    Mapping,
    MutableMapping,
    Optional,
    Sequence,
    TYPE_CHECKING,
)

# 型チェック時のみ psycopg の型情報を取り込む
if TYPE_CHECKING:
    import psycopg  # noqa: F401
    from psycopg.rows import BaseRow  # noqa: F401

try:
    import psycopg  # type: ignore
    from psycopg.rows import dict_row  # type: ignore
except ModuleNotFoundError:
    psycopg = None  # type: ignore
    dict_row = None  # type: ignore

from .base import BaseRepository

logger = logging.getLogger(__name__)


def _get_env_var(name: str) -> str | None:
    """環境変数（bytes 版も含む）から文字列を取得"""
    if name in os.environ:
        return os.environ[name]
    environb: MutableMapping[bytes, bytes] | None = getattr(os, "environb", None)
    if environb and (bname := name.encode()) in environb:
        raw = environb[bname]
        try:
            return raw.decode()
        except UnicodeDecodeError:
            return raw.decode("cp932", "ignore")
    return None


def _env(primary: str, fallback: str, default: str = "") -> str:
    return os.getenv(primary) or os.getenv(fallback) or default


def _make_dsn() -> str | Dict[str, Any]:
    """PG_DSN or DATABASE_URL があれば文字列で返し、
    なければ個別項目から dict を組み立てる"""
    if dsn := _get_env_var("PG_DSN"):
        return dsn
    if dsn := _get_env_var("DATABASE_URL"):
        return dsn
    return {
        "host": _env("PG_HOST", "POSTGRES_HOST", "db"),
        "port": int(_env("PG_PORT", "POSTGRES_PORT", "5432")),
        "dbname": _env("PG_DB", "POSTGRES_DB", "mmopdca"),
        "user": _env("PG_USER", "POSTGRES_USER", "mmopdca"),
        "password": _env("PG_PASSWORD", "POSTGRES_PASSWORD", "secret"),
    }


# コネクションは Any 扱い（実行時に psycopg がなければ runtime error）
_CX: Optional[Any] = None


def _cx() -> Any:  # type: ignore[return]
    """シングルトンで psycopg.Connection を返す"""
    global _CX
    if _CX is None or getattr(_CX, "closed", True):
        if psycopg is None:
            raise RuntimeError(
                "psycopg がインストールされていません。\n"
                "DB_BACKEND を memory/sqlite/redis に変更するか "
                "`poetry install --with db` を実行してください。"
            )
        dsn = _make_dsn()
        _CX = (
            psycopg.connect(dsn, autocommit=True)
            if isinstance(dsn, str)
            else psycopg.connect(autocommit=True, **dsn)
        )
    return _CX


class PostgresRepository(BaseRepository):
    """
    PostgreSQL(JSONB) Repository。

    • eager=False の時は DDL/接続を遅延 → pytest で実 DB が不要
    • tenant_id + id = 複合 PK、data カラムに JSONB 保存
    """

    tenant_id: str = ""

    def __init__(
        self,
        *,
        table: str,
        schema: str = "public",
        eager: bool = False,
    ) -> None:
        super().__init__(table=table)
        self.table = table
        self.schema = schema
        self._initialized = False
        if eager:
            self._ensure_table()

    def _ensure_table(self) -> None:
        """最初の操作時にスキーマ・テーブルを作成"""
        if self._initialized:
            return
        ddl = f'''
        CREATE SCHEMA IF NOT EXISTS "{self.schema}";
        CREATE TABLE IF NOT EXISTS "{self.schema}"."{self.table}" (
            tenant_id  TEXT        NOT NULL DEFAULT '',
            id         TEXT        NOT NULL,
            data       JSONB       NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            PRIMARY KEY (tenant_id, id)
        );
        '''
        with _cx().cursor() as cur:
            cur.execute(ddl)
        self._initialized = True

    def _lazy(self) -> None:
        """初回アクセス時にテーブルを確実に用意"""
        if not self._initialized:
            self._ensure_table()

    def create(self, obj_id: str, data: Mapping[str, Any]) -> None:
        """INSERT あるいは UPDATE (upsert)"""
        self._lazy()
        sql = (
            f'INSERT INTO "{self.schema}"."{self.table}" (tenant_id,id,data) '
            "VALUES (%s,%s,%s) "
            "ON CONFLICT (tenant_id,id) DO UPDATE SET data = EXCLUDED.data"
        )
        with _cx().cursor() as cur:
            cur.execute(sql, (self.tenant_id, obj_id, json.dumps(dict(data))))

    update = create  # upsert alias

    def get(self, obj_id: str) -> Optional[Dict[str, Any]]:
        """キーに対応する JSON を取得"""
        self._lazy()
        sql = (
            f'SELECT data FROM "{self.schema}"."{self.table}" '
            "WHERE tenant_id=%s AND id=%s"
        )
        with _cx().cursor(row_factory=dict_row) as cur:  # type: ignore[arg-type]
            cur.execute(sql, (self.tenant_id, obj_id))
            row = cur.fetchone()
        return dict(row["data"]) if row else None

    def delete(self, obj_id: str) -> None:
        """キーを削除"""
        self._lazy()
        sql = (
            f'DELETE FROM "{self.schema}"."{self.table}" '
            "WHERE tenant_id=%s AND id=%s"
        )
        with _cx().cursor() as cur:
            cur.execute(sql, (self.tenant_id, obj_id))

    def list(self) -> List[Dict[str, Any]]:
        """このテナントの全エントリを降順で取得"""
        self._lazy()
        sql = (
            f'SELECT data FROM "{self.schema}"."{self.table}" '
            "WHERE tenant_id=%s ORDER BY created_at DESC"
        )
        with _cx().cursor(row_factory=dict_row) as cur:  # type: ignore[arg-type]
            cur.execute(sql, (self.tenant_id,))
            rows = cur.fetchall()
        return [dict(r["data"]) for r in rows]
