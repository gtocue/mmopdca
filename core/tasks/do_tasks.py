# =========================================================
# File: core/tasks/do_tasks.py
# Name: Do フェーズの Celery タスク実装
# =========================================================

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict

from core.celery_app import celery_app
from core.do.coredo_executor import run_do
from core.repository.factory import get_repo
from core.schemas.do_schemas import DoStatus

logger = logging.getLogger(__name__)
_do_repo = get_repo("do")


def _upsert(do_id: str, rec: Dict[str, Any]) -> None:
    """単純な delete → create で擬似 upsert。"""
    try:
        _do_repo.delete(do_id)
    except Exception:
        # 存在しない場合などは無視
        pass
    _do_repo.create(do_id, rec)


# ----------------------------------------------------------------------
# テスト用：Heartbeat を毎分プリントするタスク
# ----------------------------------------------------------------------
@celery_app.task(name="core.tasks.do_tasks.print_heartbeat")
def print_heartbeat() -> None:
    """
    定期的に heartbeat を標準出力に出すテスト用タスク。
    UTC のタイムスタンプを [heartbeat] タグ付きで出力します。
    """
    ts = datetime.now(timezone.utc).isoformat()
    print(f"[heartbeat] {ts}")


# ----------------------------------------------------------------------
# メイン：Do フェーズを実行するタスク
# ----------------------------------------------------------------------
@celery_app.task(
    name="core.tasks.do_tasks.run_do_task",
    acks_late=True,
    max_retries=3,
    autoretry_for=(Exception,),
    retry_backoff=True,
)
def run_do_task(do_id: str, plan_id: str, params: dict) -> None:  # noqa: ANN001
    """
    Do フェーズを実行し、リポジトリにステータスと結果を記録する Celery タスク。
    """
    now = datetime.now(timezone.utc).isoformat()

    # 1) RUNNING へ
    _upsert(
        do_id,
        {
            "do_id": do_id,
            "plan_id": plan_id,
            "status": DoStatus.RUNNING.value,
            "updated_at": now,
        },
    )

    try:
        # 2) 実処理
        result = run_do(plan_id, params)

        # 3) DONE
        _upsert(
            do_id,
            {
                "do_id": do_id,
                "plan_id": plan_id,
                "status": DoStatus.DONE.value,
                "result": result,
                "completed_at": datetime.now(timezone.utc).isoformat(),
            },
        )

    except Exception as exc:
        logger.error("Do task failed: %s", exc, exc_info=True)
        # 4) FAILED
        _upsert(
            do_id,
            {
                "do_id": do_id,
                "plan_id": plan_id,
                "status": DoStatus.FAILED.value,
                "error": str(exc),
                "completed_at": datetime.now(timezone.utc).isoformat(),
            },
        )
        # リトライのため例外を再送出
        raise
