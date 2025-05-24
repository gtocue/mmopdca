# =========================================================
# core/tasks/check_tasks.py
# =========================================================
#
# Check フェーズの Celery タスク実装
#   - Do フェーズの結果を評価し、レポジトリにレポートを記録
#
# run_check_task:
#   • PENDING → RUNNING → SUCCESS/FAILURE を管理
#   • Do フェーズの完了待ち & メトリクス充足待ち
#   • SQLiteRepository は delete/create で upsert
#   • datetime は UTC ISO8601形式
# ---------------------------------------------------------

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List


from celery.exceptions import Retry
from core.celery_app import celery_app
from core.repository.factory import get_repo
from core.schemas.check_schemas import CheckReport
from core.schemas.do_schemas import DoStatus  # Do フェーズの状態定義

logger = logging.getLogger(__name__)
_check_repo = get_repo("check")
_do_repo = get_repo("do")


def _upsert(check_id: str, rec: Dict[str, Any]) -> None:
    """
    同 ID があれば削除し、新規レコードを作成して upsert を実現
    """
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
        "id": check_id,
        "do_id": do_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    rec.update(
        {
            "status": "RUNNING",
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    _upsert(check_id, rec)

    try:
        # 2) Do フェーズ結果取得
        rec_do = _do_repo.get(do_id) or {}

        # 2.1) Do フェーズが完了しているかチェック
        status_do = rec_do.get("status")
        if status_do != DoStatus.DONE:
            logger.info("Do status=%s, retrying…", status_do)
            # カウントダウンしてリトライ
            raise self.retry(countdown=3)

        result_payload = rec_do.get("result", {})

                # --- metrics dict をフラット化 ----------------------------------
        # run_do_task の戻り値では各指標が ``metrics`` にネストされている。
        # 古いフォーマットではトップレベルに直接存在していたため、双方の
        # 形式を許容するよう ``metrics`` があれば展開しておく。
        if isinstance(result_payload.get("metrics"), dict):
            result_payload = {
                **result_payload,
                **result_payload["metrics"],
            }

        # 2.2) 必須メトリクス揃い待ち
        required: List[str] = ["r2", "threshold", "passed"]
        missing = [k for k in required if k not in result_payload]
        if missing:
            logger.info("Metrics missing: %s, retrying…", missing)
            raise self.retry(countdown=3)

        # 3) Pydantic でバリデート＆レポート生成
        report = CheckReport(**result_payload)

        # 4) SUCCESS と report を保存
        rec = _check_repo.get(check_id) or {}
        rec.update(
            {
                "status": report.status,
                "report": report.model_dump(),
                "completed_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        _upsert(check_id, rec)

    except Retry:
        # Retry は Celery に再スケジュールさせるためそのまま伝搬
        raise
    except Exception as exc:
        # 5) 例外時は FAILURE とエラーメッセージを保存
        logger.error("Check task failed: %s", exc, exc_info=True)
        rec = _check_repo.get(check_id) or {}
        rec.update(
            {
                "status": "FAILURE",
                "error": str(exc),
                "completed_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        _upsert(check_id, rec)
        # Celery にも例外として伝搬
        raise
