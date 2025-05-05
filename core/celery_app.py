# =========================================================
# ASSIST_KEY: 【core/celery_app.py】
# =========================================================
# * broker / backend               : 環境変数で指定（デフォルト redis）
# * すべて JSON シリアライズ
# * core.tasks.* を autodiscover
# * Do-phase 用 run_do_task を “run_do” エイリアスでも公開
# =========================================================

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict

from celery import Celery

# ──────────────────────────────── logger
logger = logging.getLogger(__name__)
if not logger.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("[%(levelname)s] %(name)s: %(message)s"))
    logger.addHandler(_h)
logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())

# ──────────────────────────────── broker / backend
BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
RESULT_BACKEND_URL: str = os.getenv("CELERY_RESULT_BACKEND", BROKER_URL)

logger.info("[Celery] bootstrap  broker=%s  backend=%s", BROKER_URL, RESULT_BACKEND_URL)

# ──────────────────────────────── Celery app
celery_app = Celery("mmopdca", broker=BROKER_URL, backend=RESULT_BACKEND_URL)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,             # Worker 落下時に再キュー
    worker_max_tasks_per_child=100,  # メモリリーク予防
    soft_time_limit=890,             # TODO: 外部設定へ
    imports=("core.tasks.do_tasks",),  # 明示 import で先読み
)

celery_app.autodiscover_tasks(["core.tasks"])

# ──────────────────────────────── Do shard task
_TOTAL_SHARDS = int(os.getenv("DO_TOTAL_SHARDS", "12"))  # TODO: 外部設定へ


@celery_app.task(
    name="run_do",  # ← 外部からはこの名前で呼ぶ
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=5,
    retry_kwargs={"max_retries": 3},
)
def run_do_task(          # noqa: D401
    self,                 # type: ignore[override]
    plan_id: str,
    params: Dict[str, Any],
    *,
    shard_idx: int = 0,
    total_shards: int = _TOTAL_SHARDS,
) -> Dict[str, Any]:
    """Shard (=epoch) 単位で実行し、残りを自己再投入する。"""
    logger.info("[Celery] run_do shard %d/%d plan=%s", shard_idx, total_shards, plan_id)

    # 遅延 import で循環依存を回避
    from core.do import checkpoint as ckpt
    from core.do.coredo_executor import run_do  # type: ignore

    # ── duplicate guard（チェックポイント側 sentinel を利用）
    if ckpt.is_done(f"{plan_id}__{params['run_no']:04d}", shard_idx):
        logger.warning("[Celery] shard %d already done – skip", shard_idx)
        return {"plan_id": plan_id, "shard": shard_idx, "status": "SKIPPED_DUPLICATE"}

    result: Dict[str, Any] = run_do(
        plan_id,
        params,
        epoch_idx=shard_idx,
        epoch_cnt=total_shards,
    )

    # ── 次 shard を予約
    if shard_idx + 1 < total_shards:
        eta_dt = datetime.utcnow() + timedelta(seconds=1)
        self.apply_async(
            args=[plan_id, params],
            kwargs={"shard_idx": shard_idx + 1, "total_shards": total_shards},
            eta=eta_dt,
        )

    return result


__all__ = ["celery_app", "run_do_task"]  # run_do でも import 可
