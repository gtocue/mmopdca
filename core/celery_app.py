# =========================================================
# core/celery_app.py
# ---------------------------------------------------------
#  • broker / backend を環境変数で切替（既定 redis）
#  • すべて JSON シリアライズ
#  • core.tasks.* を autodiscover
#  • Do-phase 用 run_do_task を “run_do” エイリアスで公開
# =========================================================
from __future__ import annotations

import logging
import os
from datetime import timedelta
from typing import Any, Dict

from celery import Celery

# ────────────────────────────────
# ロガー
# ────────────────────────────────
logger = logging.getLogger(__name__)
if not logger.handlers:  # 多重登録防止
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter("[%(levelname)s] %(name)s: %(message)s"))
    logger.addHandler(h)
logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())

# ────────────────────────────────
# broker / backend
# ────────────────────────────────
BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
RESULT_BACKEND_URL = os.getenv("CELERY_RESULT_BACKEND", BROKER_URL)

logger.info("[Celery] bootstrap  broker=%s  backend=%s", BROKER_URL, RESULT_BACKEND_URL)

# ────────────────────────────────
# Celery インスタンス
# ────────────────────────────────
celery_app = Celery("mmopdca", broker=BROKER_URL, backend=RESULT_BACKEND_URL)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,             # ワーカー落下時の再処理
    worker_max_tasks_per_child=100,  # メモリリーク対策
    soft_time_limit=890,             # TODO: 外部設定へ
        # ↓↓↓ これを追加 ↓↓↓
    imports=("core.tasks.do_tasks",),        # ★ ここ！
)

# ────────────────────────────────
# タスク自動検出
# ────────────────────────────────
celery_app.autodiscover_tasks(["core.tasks"])

# ────────────────────────────────
# Do-phase shard 実行タスク
#   – run_do_task を “run_do” 名でも公開
# ────────────────────────────────
_TOTAL_SHARDS = int(os.getenv("DO_TOTAL_SHARDS", "12"))  # TODO: 外部設定へ


@celery_app.task(
    name="run_do",      # public 名
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=5,
    retry_kwargs={"max_retries": 3},
)
def run_do_task(  # noqa: D401
    self,                       # type: ignore[override]
    plan_id: str,
    params: Dict[str, Any],
    *,
    shard_idx: int = 0,
    total_shards: int = _TOTAL_SHARDS,
) -> Dict[str, Any]:
    """Do-phase を shard (=epoch) 単位で実行し、自分で次 shard を投げ直す。"""
    logger.info("[Celery] run_do shard %d/%d plan=%s", shard_idx, total_shards, plan_id)

    # 遅延 import で循環依存回避
    from core.do.coredo_executor import run_do  # type: ignore

    result = run_do(plan_id, params, epoch_idx=shard_idx, epoch_cnt=total_shards)

    # 残 shard があれば自己再投入
    if shard_idx + 1 < total_shards:
        eta = timedelta(seconds=1)
        self.apply_async(
            args=[plan_id, params],
            kwargs={"shard_idx": shard_idx + 1, "total_shards": total_shards},
            eta=self.datetime.utcnow() + eta,
        )

    return result


__all__ = ["celery_app", "run_do_task"]  # “run_do” でも import 可
