# =========================================================
# ASSIST_KEY: このファイルは【core/repository/sqlite_impl.py】に位置するユニットです
# =========================================================
#
# 【概要】
#   SQLite 永続化レポジトリ（汎用 key-value ストア）
#   - BaseRepository を継承して create / get / list / delete を実装
#
# ---------------------------------------------------------

from __future__ import annotations

import json
import sqlite3
from typing import Any, Dict

from .base import BaseRepository

# --------------------------------------------------
# SQLiteRepository
# --------------------------------------------------
class SQLiteRepository(BaseRepository):
    """
    任意テーブルを {id TEXT PRIMARY KEY, data TEXT(JSON)} スキーマで保存する
    """

    def __init__(self, path: str = "mmopdca.db", table: str = "plan") -> None:
        # テーブル名をダブルクォートで必ずエスケープ
        self.table: str = table
        self.quoted: str = f'"{table}"'

        # NOTE: check_same_thread=False ⇒ FastAPI のスレッド間共有を許可
        self.conn = sqlite3.connect(path, check_same_thread=False)

        # テーブル作成
        self.conn.execute(
            f"CREATE TABLE IF NOT EXISTS {self.quoted} ("
            "id TEXT PRIMARY KEY, "
            "data TEXT NOT NULL)"
        )
        self.conn.commit()

    # ----------------- CRUD -----------------
    def create(self, obj_id: str, data: Dict[str, Any]) -> None:
        self.conn.execute(
            f"INSERT OR REPLACE INTO {self.quoted}(id, data) VALUES(?, ?)",
            (obj_id, json.dumps(data, ensure_ascii=False)),
        )
        self.conn.commit()

    def get(self, obj_id: str) -> Dict[str, Any] | None:
        cur = self.conn.execute(
            f"SELECT data FROM {self.quoted} WHERE id = ?", (obj_id,)
        )
        row = cur.fetchone()
        return json.loads(row[0]) if row else None

    def list(self) -> list[Dict[str, Any]]:
        cur = self.conn.execute(f"SELECT data FROM {self.quoted}")
        return [json.loads(r[0]) for r in cur.fetchall()]

    def delete(self, obj_id: str) -> None:
        self.conn.execute(f"DELETE FROM {self.quoted} WHERE id = ?", (obj_id,))
        self.conn.commit()

    # ----------------- housekeeping -----------------
    def __del__(self) -> None:  # noqa: D401
        try:
            self.conn.close()
        except Exception:  # pragma: no cover
            pass
