# =========================================================
# ASSIST_KEY: 【core/celery_app.py】
# =========================================================
#
# 【概要】
#   Celery アプリケーション本体。
#   - broker / backend を .env で切り替え（デフォルト redis）
#   - すべてのタスクを JSON シリアライズに統一
#   - core.tasks.* を autodiscover して拡張タスクを自動登録
#   - Do-phase 用 run_do_task を “run_do” エイリアスで公開
#
# 【主な役割】
#   - Celery インスタンス生成・設定
#   - run_do_task (≤15 min 制限対応のシャーディング) を提供
#
# 【連携先・依存関係】
#   - core.do.coredo_executor.run_do … ビジネスロジック
#   - api/routers/do_api.py          … enqueue → Celery publish
#
# 【ルール遵守】
#   1) ハードコード値には “TODO: 外部設定へ” を必ず付記
#   2) 機能削除・breaking change 禁止（追加のみ）
#   3) typing を明示。logger を使用し print() 禁止
# ---------------------------------------------------------

from __future__ import annotations

import logging
import os
from datetime import timedelta
from typing import Any, Dict

from celery import Celery

# ------------------------------------------------------------------ #
# ログ設定
# ------------------------------------------------------------------ #
logger = logging.getLogger(__name__)
if not logger.handlers:  # 再 import 時の多重追加を防止
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("[%(levelname)s] %(name)s: %(message)s"))
    logger.addHandler(_h)
logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())

# ------------------------------------------------------------------ #
# broker / backend URL
# ------------------------------------------------------------------ #
BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
RESULT_BACKEND_URL: str = os.getenv("CELERY_RESULT_BACKEND", BROKER_URL)

logger.info("[Celery] bootstrap broker=%s backend=%s", BROKER_URL, RESULT_BACKEND_URL)

# ------------------------------------------------------------------ #
# Celery インスタンス
# ------------------------------------------------------------------ #
celery_app: Celery = Celery("mmopdca", broker=BROKER_URL, backend=RESULT_BACKEND_URL)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,             # ワーカー落下時に再キュー
    worker_max_tasks_per_child=100,  # メモリリーク対策
    soft_time_limit=890,             # ← TODO: 外部設定へ (15 min - 10 s)
)

# ------------------------------------------------------------------ #
# タスク自動検出
# ------------------------------------------------------------------ #
celery_app.autodiscover_tasks(["core.tasks"])

# ------------------------------------------------------------------ #
# Do-phase 実行タスク (≤15 min シャーディング対応)
# ------------------------------------------------------------------ #
_SHARDS: int = int(os.getenv("DO_TOTAL_SHARDS", "12"))  # TODO: 外部設定へ


@celery_app.task(
    name="run_do",                  # public 露出名を固定
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=5,
    retry_kwargs={"max_retries": 3},
)
def run_do_task(                    # noqa: D401 – Celery signature
    self,                           # type: ignore[override]
    plan_id: str,
    params: Dict[str, Any],
    *,
    shard_idx: int = 0,
    total_shards: int = _SHARDS,
) -> Dict[str, Any]:
    """
    **Do-phase** を shard (=epoch) 単位で実行し、残 shard があれば
    自身を再投入する。

    Parameters
    ----------
    plan_id      : str
    params       : dict[str, Any] – Do ルータ生成引数
    shard_idx    : int            – 現在 shard (0-based)
    total_shards : int            – 全 shard 数
    """
    logger.info("[Celery] run_do shard %d/%d plan=%s", shard_idx, total_shards, plan_id)

    # 遅延 import で起動高速化 & 循環依存回避
    from core.do.coredo_executor import run_do  # type: ignore

    result = run_do(
        plan_id,
        params,
        epoch_idx=shard_idx,
        epoch_cnt=total_shards,
    )

    # 次 shard が残っていれば自己再投入
    if shard_idx + 1 < total_shards:
        eta = timedelta(seconds=1)  # ほぼ即時
        self.apply_async(
            args=[plan_id, params],
            kwargs=dict(shard_idx=shard_idx + 1, total_shards=total_shards),
            eta=self.datetime.utcnow() + eta,
        )

    return result


__all__ = ["celery_app", "run_do_task"]
