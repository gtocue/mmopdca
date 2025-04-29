# =========================================================
# core/repository/base.py
# =========================================================
#
# 共通 Repository インターフェース
# --------------------------------
# * すべての Repository 実装（memory / sqlite / postgres …）の親。
# * マルチテナント対応を見据えて `tenant_id` を追加。
# * CRUD のシグネチャのみ定義し、実装は各サブクラスへ委譲。
# ---------------------------------------------------------

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class BaseRepository(ABC):
    """
    抽象 Repository 基底クラス

    Parameters
    ----------
    table : str
        対象となるテーブル名・コレクション名など。
    tenant_id : str, default ''
        マルチテナント用 ID。シングルテナントの場合は空文字列。
    """

    def __init__(self, *, table: str, tenant_id: str = "") -> None:
        self.table: str = table
        self.tenant_id: str = tenant_id

    # -----------------------------------------------------
    # CRUD 抽象メソッド
    # -----------------------------------------------------
    @abstractmethod
    def create(self, obj_id: str, data: Dict[str, Any]) -> None:
        """id をキーにオブジェクトを保存（同 ID があれば上書き）"""
        raise NotImplementedError

    @abstractmethod
    def get(self, obj_id: str) -> Dict[str, Any] | None:
        """id で 1 件取得。無ければ None"""
        raise NotImplementedError

    @abstractmethod
    def list(self) -> List[Dict[str, Any]]:
        """tenant 内のオブジェクトを新しい順で一覧取得"""
        raise NotImplementedError

    @abstractmethod
    def delete(self, obj_id: str) -> None:
        """id を指定して削除（存在しなくてもエラーにしない）"""
        raise NotImplementedError
