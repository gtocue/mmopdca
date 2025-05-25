# =========================================================
# ASSIST_KEY: core/repository/sqlite_impl.py
# =========================================================
#
# SQLite 汎用 JSON ストア（tenant_id, id, data, created_at）
# -----------------------------------------------------------

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List

from .base import BaseRepository

_SQLITE_PRAGMA_FK = "PRAGMA foreign_keys = ON;"


class SQLiteRepository(BaseRepository):
    """
    {tenant_id, id} を複合 PK にした JSON ストア Repository
    """

    def __init__(
        self,
        path: str | Path = "mmopdca.db",
        table: str = "plan",
        tenant_id: str = "public",
    ) -> None:
        self.table = table
        self.tenant_id = tenant_id
        self.quoted = f'"{table}"'

        self.conn = sqlite3.connect(str(path), check_same_thread=False)
        self.conn.execute(_SQLITE_PRAGMA_FK)

        self._ensure_schema()

    # ------------------------------------------------------------------ #
    # スキーマ保証
    # ------------------------------------------------------------------ #
    def _ensure_schema(self) -> None:
        with self.conn:  # autocommit
            # ① 新規作成
            self.conn.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {self.quoted} (
                    tenant_id  TEXT NOT NULL DEFAULT 'public',
                    id         TEXT NOT NULL,
                    data       TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (tenant_id, id)
                );
                """
            )

            # ② 旧テーブル救済（列追加）
            cols = {
                row[1]  # (cid, name, type, notnull, dflt_value, pk)
                for row in self.conn.execute(
                    f"PRAGMA table_info({self.quoted});"
                ).fetchall()
            }
            if "tenant_id" not in cols:
                self.conn.execute(
                    f"""
                    ALTER TABLE {self.quoted}
                    ADD COLUMN tenant_id TEXT NOT NULL DEFAULT 'public';
                """
                )
                # 既存 PK(id) を複合 PK に作り直すのは難しいため、
                # 移行時は dump/restore を推奨（MVP ではスキップ）

            # ③ created_at 降順インデックス
            self.conn.execute(
                f"""
                CREATE INDEX IF NOT EXISTS idx_{self.table}__tenant_created_at
                ON {self.quoted}(tenant_id, created_at DESC);
                """
            )

    # ------------------------------------------------------------------ #
    # CRUD
    # ------------------------------------------------------------------ #
    def create(self, obj_id: str, data: Dict[str, Any]) -> None:
        with self.conn:
            self.conn.execute(
                f"""
                INSERT OR REPLACE INTO {self.quoted}
                    (tenant_id, id, data)
                VALUES(?, ?, ?)
                """,
                (self.tenant_id, obj_id, json.dumps(data, ensure_ascii=False)),
            )

    def get(self, obj_id: str) -> Dict[str, Any] | None:
        cur = self.conn.execute(
            f"""
            SELECT data FROM {self.quoted}
            WHERE tenant_id = ? AND id = ?
            """,
            (self.tenant_id, obj_id),
        )
        row = cur.fetchone()
        return json.loads(row[0]) if row else None

    def list(self) -> List[Dict[str, Any]]:
        cur = self.conn.execute(
            f"""
            SELECT data FROM {self.quoted}
            WHERE tenant_id = ?
            ORDER BY created_at DESC
            """,
            (self.tenant_id,),
        )
        return [json.loads(r[0]) for r in cur.fetchall()]

    def delete(self, obj_id: str) -> None:
        with self.conn:
            self.conn.execute(
                f"""
                DELETE FROM {self.quoted}
                WHERE tenant_id = ? AND id = ?
                """,
                (self.tenant_id, obj_id),
            )

    def exists(self, obj_id: str) -> bool:
        cur = self.conn.execute(
            f"SELECT 1 FROM {self.quoted} WHERE tenant_id = ? AND id = ? LIMIT 1",
            (self.tenant_id, obj_id),
        )
        return cur.fetchone() is not None

    # ------------------------------------------------------------------ #
    # housekeeping
    # ------------------------------------------------------------------ #
    def __del__(self) -> None:  # noqa: D401
        try:
            self.conn.close()
        except Exception:  # pragma: no cover
            pass
