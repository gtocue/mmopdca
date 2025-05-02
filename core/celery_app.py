# ======================================================================
# core/celery_app.py
# ----------------------------------------------------------------------
#   Celery アプリケーション本体
#   * broker / backend → 環境変数で切替（デフォルト: redis）
#   * JSON シリアライズを強制
#   * core.tasks.* 以下を autodiscover
#   * run_do_task を “run_do” エイリアスで公開
# ======================================================================

from __future__ import annotations

import logging
import os
from typing import Any, Dict

from celery import Celery

# ------------------------------------------------------------------ #
# ログ設定
# ------------------------------------------------------------------ #
logger = logging.getLogger(__name__)
if not logger.handlers:  # 再 import 時に二重登録させない
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter("[%(levelname)s] %(name)s: %(message)s")
    )
    logger.addHandler(handler)

logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())

# ------------------------------------------------------------------ #
# broker / backend URL
# ------------------------------------------------------------------ #
BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
RESULT_BACKEND_URL: str = os.getenv("CELERY_RESULT_BACKEND", BROKER_URL)

logger.info(
    "[Celery] bootstrap  broker=%s  backend=%s",
    BROKER_URL,
    RESULT_BACKEND_URL,
)

# ------------------------------------------------------------------ #
# Celery インスタンス
# ------------------------------------------------------------------ #
celery_app: Celery = Celery(
    "mmopdca",
    broker=BROKER_URL,
    backend=RESULT_BACKEND_URL,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,            # ワーカー落下/kill 時に再キュー
    worker_max_tasks_per_child=100, # メモリリーク対策
)

# ------------------------------------------------------------------ #
# タスク自動登録: core.tasks パッケージを再帰探索
# ------------------------------------------------------------------ #
celery_app.autodiscover_tasks(["core.tasks"])

# ------------------------------------------------------------------ #
# Do フェーズ実行タスク（エイリアス名を固定したいので明示定義）
# ------------------------------------------------------------------ #
@celery_app.task(
    name="run_do",                    # public キュー名
    autoretry_for=(Exception,),       # 失敗時に自動リトライ
    retry_backoff=5,                  # 5s → 10s → 20s ...
    retry_kwargs={"max_retries": 3},
)
def run_do_task(plan_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    非同期 “Do-phase” 実行タスク。

    Parameters
    ----------
    plan_id : str
        実行対象 Plan の ID
    params  : dict[str, Any]
        Do ルータで生成したパラメータ辞書（symbol・期間など）

    Returns
    -------
    dict[str, Any]
        core.do.coredo_executor.run_do が返す JSON 互換辞書
    """
    logger.info("[Celery] run_do_task start  plan=%s", plan_id)

    # 遅延 import ― 起動時間短縮 & 循環依存回避
    from core.do.coredo_executor import run_do  # noqa: WPS433 (import inside def)

    result = run_do(plan_id, params)

    logger.info(
        "[Celery] run_do_task done   plan=%s   rows=%s",
        plan_id,
        result.get("summary", {}).get("rows"),
    )
    return result


# ------------------------------------------------------------------ #
# (参考) Beat 定期タスクテンプレ
# ------------------------------------------------------------------ #
# from celery.schedules import crontab
#
# celery_app.conf.beat_schedule = {
#     "daily-health-check": {
#         "task": "run_health_check",
#         "schedule": crontab(minute=0, hour=3),  # 毎日 03:00 (UTC)
#     }
# }
#
# @celery_app.task(name="run_health_check")
# def run_health_check() -> str:  # pragma: no cover
#     logger.info("[Celery] health-check ping")
#     return "pong"


__all__ = ["celery_app", "run_do_task"]
