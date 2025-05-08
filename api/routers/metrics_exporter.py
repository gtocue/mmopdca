# =========================================================
# ASSIST_KEY: 【api/routers/metrics_exporter.py】
# =========================================================
#
# Prometheus Exporter – /metrics エンドポイントに
# r2 / mae / rmse / mape を Gauge 形式で公開するサブアプリ。
#
# 【主な修正】
#   1) APIRouter 経由をやめ、FastAPI サブアプリを直接 mount("/")
#      → FastAPIError「Prefix and path cannot be both empty」を解消。
#   2) exporter 側の docs / redoc / openapi を無効化（ノイズ削減）。
#   3) Repository I/F が統一されるまで latest()/list()/keys() を順に探索。
#
# 【ルール】
#   - 指標名には “pdca_***” プレフィクスを必ず付ける
#   - 10 秒おきのバックグラウンド thread で最新 1 件のみ pull
#   - ビジネス API とは疎結合。依存は core.repository.factory のみ
# ---------------------------------------------------------

from __future__ import annotations

import logging
import os
import time
from threading import Thread
from typing import Dict, Mapping, Sequence

from fastapi import FastAPI
from prometheus_client import Gauge, make_asgi_app

from core.repository.factory import get_repo  # ← あなたの RepoFactory

# --------------------------------------------------------------------------- #
# logger
# --------------------------------------------------------------------------- #
logger = logging.getLogger(__name__)
logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())

# --------------------------------------------------------------------------- #
# Prometheus Gauges
# --------------------------------------------------------------------------- #
_METRIC_GAUGES: Dict[str, Gauge] = {
    "r2":   Gauge("pdca_r2",   "R-squared of latest run"),
    "mae":  Gauge("pdca_mae",  "Mean Absolute Error of latest run"),
    "rmse": Gauge("pdca_rmse", "Root Mean Squared Error of latest run"),
    "mape": Gauge("pdca_mape", "Mean Absolute Percentage Error (pct)"),
}

# Repository インスタンス（MemoryRepository / RedisRepository など想定）
_metrics_repo = get_repo("metrics")  # TODO: DI で差し替え可能に


# --------------------------------------------------------------------------- #
# helper – 最新レコード 1 件を取得
# --------------------------------------------------------------------------- #
def _fetch_latest() -> Mapping[str, float] | None:
    """
    Repository 実装差異を吸収しつつ「最新 1 件」を返す。

    優先度:
      1) latest()  … 1件だけ返す想定の正式 API
      2) list()    … list()[0] を最新扱い（ソート済み前提）
      3) keys()    … 昔の仮実装
    """
    if hasattr(_metrics_repo, "latest"):
        return _metrics_repo.latest()  # type: ignore[attr-defined]

    if hasattr(_metrics_repo, "list"):
        items: Sequence[Mapping[str, float]] = _metrics_repo.list()  # type: ignore[attr-defined]
        return items[0] if items else None

    if hasattr(_metrics_repo, "keys") and hasattr(_metrics_repo, "get"):
        keys: Sequence[str] = sorted(_metrics_repo.keys(), reverse=True)  # type: ignore[attr-defined]
        return _metrics_repo.get(keys[0]) if keys else None  # type: ignore[attr-defined]

    logger.warning("[MetricsExporter] repo has no iterable API – skip")
    return None


# --------------------------------------------------------------------------- #
# background thread – Gauge update loop
# --------------------------------------------------------------------------- #
def _poll_latest_metrics(interval: int = 10) -> None:  # pragma: no cover
    while True:
        try:
            latest = _fetch_latest()
            if latest:
                for name, gauge in _METRIC_GAUGES.items():
                    gauge.set(float(latest.get(name, 0.0)))
        except Exception as exc:  # noqa: BLE001
            logger.warning("[MetricsExporter] polling error: %s", exc)

        time.sleep(interval)


# --------------------------------------------------------------------------- #
# factory – create FastAPI sub-application
# --------------------------------------------------------------------------- #
def create_metrics_exporter() -> FastAPI:
    """
    /metrics 用 FastAPI サブアプリを生成して返す。

    Returns
    -------
    FastAPI
        Prometheus exporter sub-application (docs 無効化済み)
    """
    exporter = FastAPI(
        title="PDCA Metrics Exporter",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )

    # prometheus_client の ASGI アプリをルートにマウント
    exporter.mount("/", make_asgi_app())

    # polling thread は 1 回だけ起動
    if os.getenv("METRICS_EXPORTER_STARTED") != "1":
        Thread(target=_poll_latest_metrics, daemon=True).start()
        os.environ["METRICS_EXPORTER_STARTED"] = "1"
        logger.info("[MetricsExporter] background polling started")

    return exporter
