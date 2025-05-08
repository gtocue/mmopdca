# =========================================================
#  core/repository/memory_impl.py
# =========================================================
"""
インメモリ実装 ― unittest やローカル開発用の軽量レポジトリ。
スレッドセーフ性は（現状の用途では）考慮していません。
"""

from __future__ import annotations

from typing import Any, Dict, List


class MemoryRepository:
    """dict ベースのシンプルな Repository。"""

    # テーブル名 → ストア(dict) のシングルトン管理
    _TABLES: Dict[str, Dict[str, Dict[str, Any]]] = {}

    # --------------------------------------------------
    # constructor
    # --------------------------------------------------
    def __init__(self, table: str = "default") -> None:
        self.table = table
        MemoryRepository._TABLES.setdefault(table, {})

    # --------------------------------------------------
    # CRUD
    # --------------------------------------------------
    def create(self, key: str, record: Dict[str, Any]) -> None:
        self._store()[key] = record

    def get(self, key: str) -> Dict[str, Any] | None:
        return self._store().get(key)

    def delete(self, key: str) -> None:
        self._store().pop(key, None)

    def list(self) -> List[Dict[str, Any]]:
        return list(self._store().values())

    # --------------------------------------------------
    # 追加分（metrics／Do 用）
    # --------------------------------------------------
    def upsert(self, key: str, record: Dict[str, Any]) -> None:
        """存在すれば更新・無ければ作成。"""
        self._store()[key] = record

    def put(self, key: str, record: Dict[str, Any]) -> None:
        """metrics_repo 互換エイリアス。"""
        self.upsert(key, record)

    def keys(self) -> List[str]:
        """登録済みキー一覧を返す。"""
        return list(self._store().keys())

    # --------------------------------------------------
    # internal
    # --------------------------------------------------
    def _store(self) -> Dict[str, Dict[str, Any]]:
        return MemoryRepository._TABLES[self.table]
