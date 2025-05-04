from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict

class BaseAdapter(ABC):
    """ドメイン固有処理を差し替える共通 I/F"""

    @abstractmethod
    def load(self, plan: Dict[str, Any]) -> Dict[str, Any]: ...
    @abstractmethod
    def plan(self, cdm: Dict[str, Any]) -> Dict[str, Any]: ...
    @abstractmethod
    def do(self, plan_dict: Dict[str, Any]) -> Dict[str, Any]: ...
    @abstractmethod
    def check(self, do_result: Dict[str, Any]) -> Dict[str, Any]: ...
    @abstractmethod
    def act(self, metrics: Dict[str, Any]) -> None: ...
