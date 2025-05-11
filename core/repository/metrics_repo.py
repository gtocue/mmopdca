# =========================================================
# ASSIST_KEY: 【core/repository/metrics_repo.py】
# =========================================================
#
# 【概要】
#   評価指標 (r2 / mae / rmse / mape …) を永続化するシンプルな
#  インメモリ実装。将来、RDB / S3 等へ差し替える際は同じ I/F を維持。
#
# 【主な役割】
#   - put(key, metrics)  : 指標レコードを保存
#   - get(key)           : 1 レコード取得
#   - keys()             : ソート用にキー一覧を返す
#   - latest()           : 直近レコードを取得（ユーティリティ）
#
# 【連携先・依存関係】
#   - core/repository/factory.py : `get_repo("metrics")` で注入
#   - api/routers/metrics_api.py : CRUD エンドポイント
#   - api/routers/metrics_exporter.py : Prometheus Exporter
#
# 【ルール遵守】
#   1) スレッドセーフではない → Gunicorn + gevent 等を想定しない
#   2) 破壊的変更を避けるため、IRepository 型に準拠
# ---------------------------------------------------------

from __future__ import annotations

import threading
from typing import Dict, List, Optional


# -------------------------------------------------------- #
# In-Memory Implementation
# -------------------------------------------------------- #
class MemoryMetricsRepository:
    """MVP 用: プロセスローカルのメトリクス格納所（揮発性）。"""

    _lock = threading.RLock()

    def __init__(self) -> None:
        self._store: Dict[str, Dict[str, float]] = {}

    # ---- CRUD ----------------------------------------------------- #
    def put(self, key: str, metrics: Dict[str, float]) -> None:
        """Upsert – 同じ key があれば上書き。"""
        with self._lock:
            self._store[key] = metrics

    def get(self, key: str) -> Optional[Dict[str, float]]:
        with self._lock:
            return self._store.get(key)

    # ---- Utilities ------------------------------------------------ #
    def keys(self) -> List[str]:
        """登録済みキー一覧（ソート用）。"""
        with self._lock:
            return list(self._store.keys())

    def latest(self) -> Optional[Dict[str, float]]:
        """一番新しいキー (= 辞書順最大) のレコードを返す。"""
        with self._lock:
            if not self._store:
                return None
            latest_key = max(self._store.keys())
            return self._store[latest_key]


# -------------------------------------------------------- #
# Factory hook  –  core.repository.factory.get_repo で使用
# -------------------------------------------------------- #
_instance: Optional[MemoryMetricsRepository] = None


def get_metrics_repo() -> MemoryMetricsRepository:
    """グローバル Singleton を返却。"""
    global _instance
    if _instance is None:
        _instance = MemoryMetricsRepository()
    return _instance
