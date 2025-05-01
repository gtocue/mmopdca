# ======================================================================
# ASSIST_KEY: 【core/celery_app.py】
# ======================================================================
#
# Celery “アプリ本体” を宣言して公開するだけのラッパーモジュール。
#  - broker / backend は .env or docker-compose 環境変数から取得
#  - JSON シリアライザをデフォルトに統一
#  - core.tasks.* 配下を autodiscover して追加タスクを自動登録
# ----------------------------------------------------------------------

from __future__ import annotations

import logging
import os
from typing import Any, Dict

from celery import Celery

# ------------------------------------------------------------------#
# ロギング
# ------------------------------------------------------------------#
logger = logging.getLogger(__name__)
if not logger.handlers:                              # 再 import 時の重複防止
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("[%(levelname)s] %(name)s: %(message)s"))
    logger.addHandler(_h)
logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())

# ------------------------------------------------------------------#
# 環境変数から broker / backend URL を取得
# ------------------------------------------------------------------#
BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
RESULT_BACKEND_URL: str = os.getenv("CELERY_RESULT_BACKEND", BROKER_URL)

logger.info(
    "[Celery] bootstrap  broker=%s  backend=%s",
    BROKER_URL,
    RESULT_BACKEND_URL,
)

# ------------------------------------------------------------------#
# Celery インスタンス生成
# ------------------------------------------------------------------#
celery_app: Celery = Celery(
    "mmopdca",
    broker=BROKER_URL,
    backend=RESULT_BACKEND_URL,
)

# 基本設定
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,               # ワーカー落下時にリキュー
    worker_max_tasks_per_child=100,    # メモリリーク対策
)

# ------------------------------------------------------------------#
# タスク auto-discover
#   core.tasks パッケージ以下に新しいタスクを置くだけで登録完了
# ------------------------------------------------------------------#
celery_app.autodiscover_tasks(["core.tasks"])

# ------------------------------------------------------------------#
# “Do フェーズ” を直接キックするシンプルなタスク
#   ※自動検出でも拾われるが、エイリアス名を固定したいので明示登録
# ------------------------------------------------------------------#
@celery_app.task(
    name="run_do",                     # 公開キュー名を固定
    autoretry_for=(Exception,),        # 失敗時自動リトライ
    retry_backoff=5,                   # 5s→10s→…指数バックオフ
    retry_kwargs={"max_retries": 3},
)
def run_do_task(plan_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    **Do-phase** を実行する Celery タスク (非同期)。

    Parameters
    ----------
    plan_id : str
        対象 Plan ID
    params  : dict
        Do API 層から渡されたパラメータ一式

    Returns
    -------
    dict
        core.do.coredo_executor.run_do が返す JSON 互換辞書
    """
    logger.info("[Celery] run_do_task start  plan=%s", plan_id)

    # 遅延 import — ワーカー起動時間短縮 & 循環依存回避
    from core.do.coredo_executor import run_do  # noqa: WPS433 (import inside def)

    result = run_do(plan_id, params)

    logger.info(
        "[Celery] run_do_task done   plan=%s   rows=%s",
        plan_id,
        result.get("summary", {}).get("rows"),
    )
    return result


# ------------------------------------------------------------------#
# (Optional) Beat 定期タスクのテンプレ
# ------------------------------------------------------------------#
# from celery.schedules import crontab
#
# celery_app.conf.beat_schedule = {
#     "daily-health-check": {
#         "task": "run_health_check",
#         "schedule": crontab(minute=0, hour=3),  # UTC 03:00
#     }
# }
#
# @celery_app.task(name="run_health_check")
# def run_health_check() -> str:  # pragma: no cover
#     logger.info("[Celery] health-check ping")
#     return "pong"
