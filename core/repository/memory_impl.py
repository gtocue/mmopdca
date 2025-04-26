# =========================================================
# ASSIST_KEY: 【core/repository/memory_impl.py】
# =========================================================
#
# インメモリ辞書で CRUD を提供するシンプル実装。
# ---------------------------------------------------------

from __future__ import annotations

from typing import Any, Dict, List

from .base import BaseRepository


class MemoryRepository(BaseRepository):
    """開発・テスト用の軽量実装（プロセス終了で消える）"""

    _GLOBAL_STORE: Dict[str, Dict[str, Dict[str, Any]]] = {}

    # ------------ CRUD ------------
    def create(self, obj_id: str, data: Dict[str, Any]) -> None:
        tbl = self._GLOBAL_STORE.setdefault(self.table, {})
        tbl[obj_id] = data

    def get(self, obj_id: str) -> Dict[str, Any] | None:
        return self._GLOBAL_STORE.get(self.table, {}).get(obj_id)

    def list(self) -> List[Dict[str, Any]]:
        return list(self._GLOBAL_STORE.get(self.table, {}).values())

    def delete(self, obj_id: str) -> None:
        self._GLOBAL_STORE.get(self.table, {}).pop(obj_id, None)
