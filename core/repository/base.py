# =========================================================
# ASSIST_KEY: 【core/repository/base.py】
# =========================================================
#
# 【概要】
#   Repository 実装の共通インターフェース。
#   create / get / list だけを抽象メソッドとして宣言します。
#
# 【主な役割】
#   - MemoryRepository / SQLiteRepository などの親クラス
#
# 【連携先】
#   - core/repository/memory_impl.py
#   - core/repository/sqlite_impl.py
#
# 【ルール】
#   1) 低レイヤなので pdca_data へは直接触れない
#   2) 型安全 (typing) を必ず付与
# ---------------------------------------------------------

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict, List


class BaseRepository(ABC):
    """Repository Interface"""

    def __init__(self, table: str):
        self.table = table

    # ---------- CRUD ----------
    @abstractmethod
    def create(self, obj_id: str, data: Dict[str, Any]) -> None: ...

    @abstractmethod
    def get(self, obj_id: str) -> Dict[str, Any] | None: ...

    @abstractmethod
    def list(self) -> List[Dict[str, Any]]: ...

    @abstractmethod
    def delete(self, obj_id: str) -> None: ...