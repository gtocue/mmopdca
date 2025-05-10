# core/tasks/check_tasks.py
# =========================================================
# Check フェーズの Celery タスク実装
#   • Do フェーズの結果を評価し、レポジトリにレポートを記録
#   • 必要なメトリクスが揃うまでリトライ
# =========================================================

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict

from core.celery_app import celery_app
from core.repository.factory import get_repo
from core.schemas.check_schemas import CheckReport

logger = logging.getLogger(__name__)
_check_repo = get_repo("check")
_do_repo    = get_repo("do")


def _upsert(check_id: str, rec: Dict[str, Any]) -> None:
    # delete/create で upsert
    try:
        _check_repo.delete(check_id)
    except Exception:
        pass
    _check_repo.create(check_id, rec)


@celery_app.task(
    name="core.tasks.check_tasks.run_check_task",
    bind=True,
    acks_late=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 10},
)
def run_check_task(self, check_id: str, do_id: str) -> None:
    """Check フェーズを実行し、レポジトリにレポートを記録する Celery タスク"""

    # 1) RUNNING 状態を保存
    rec = _check_repo.get(check_id) or {
        "id":         check_id,
        "do_id":      do_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    rec.update({
        "status":     "RUNNING",
        "updated_at": datetime.now(timezone.utc).isoformat(),
    })
    _upsert(check_id, rec)

    # 2) Do フェーズ結果取得
    rec_do = _do_repo.get(do_id)
    if rec_do is None or rec_do.get("result") is None:
        # まだ Do の結果が来ていない
        logger.info("Do result not found, retrying check: %s", do_id)
        raise self.retry(countdown=3)

    result_payload: Dict[str, Any] = rec_do["result"]

    # 3) メトリクスが揃っているかチェック
    #    run_check(do)→ result に status="SUCCESS" と必須フィールドが揃っている想定
    if result_payload.get("status") != "SUCCESS" or \
       not all(k in result_payload for k in ("r2", "threshold", "passed")):
        logger.info("Check not ready (status=%s), retrying...", result_payload.get("status"))
        raise self.retry(countdown=3)

    try:
        # 4) Pydantic で最終バリデーション＆レポート生成
        report = CheckReport(**result_payload)

        # 5) SUCCESS と report を保存
        rec = _check_repo.get(check_id) or {}
        rec.update({
            "status":       report.status,
            "report":       report.model_dump(),
            "completed_at": datetime.now(timezone.utc).isoformat(),
        })
        _upsert(check_id, rec)

    except Exception as exc:
        # 6) 例外時は FAILURE とエラーを保存
        logger.error("Check task failed permanently: %s", exc, exc_info=True)
        rec = _check_repo.get(check_id) or {}
        rec.update({
            "status":       "FAILURE",
            "error":        str(exc),
            "completed_at": datetime.now(timezone.utc).isoformat(),
        })
        _upsert(check_id, rec)
        raise
