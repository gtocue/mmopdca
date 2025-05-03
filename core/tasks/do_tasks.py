# =====================================================================
# core/tasks/do_tasks.py
# ---------------------------------------------------------------------
# “Do フェーズ” をバックグラウンドで実行するエントリポイント。
#
#  ▸ Celery がインストール済み ───────────────────────────
#      shared_task で登録し、 .apply_async で enqueue。
#
#  ▸ Celery が無い／使わない ───────────────────────────
#      フォールバック実装 (SyncTask) が即時に run_do() を呼び、
#      呼び出し側からは同じ .apply_async インタフェースが見える。
# =====================================================================
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict

from core.dsl.loader import PlanLoader
from core.repository.factory import get_repo
from core.do.coredo_executor import run_do

logger = logging.getLogger(__name__)

# ────────────────────────────────
# Repository
# ────────────────────────────────
_do_repo = get_repo(table="do")

# ────────────────────────────────
# Celery 判定
# ────────────────────────────────
try:
    from celery import shared_task, Task  # type: ignore
    from core.celery_app import celery_app

    _HAS_CELERY = True
except ModuleNotFoundError:  # pragma: no cover
    _HAS_CELERY = False
    shared_task = None  # type: ignore
    Task = object       # type: ignore

# ────────────────────────────────
# 内部ヘルパ
# ────────────────────────────────
def _upsert(rec: Dict[str, Any]) -> None:
    _do_repo.delete(rec["do_id"])
    _do_repo.create(rec["do_id"], rec)


def _execute(do_id: str, plan_id: str, params: Dict[str, Any]) -> None:
    rec = _do_repo.get(do_id) or {}
    rec.update(status="RUNNING", started_at=datetime.now(timezone.utc).isoformat())
    _upsert(rec)

    try:
        result = run_do(plan_id, params)
        rec.update(status="DONE", finished_at=datetime.now(timezone.utc).isoformat(), result=result)
        logger.info("[Do] ✓ %s DONE", do_id)
    except Exception as exc:  # noqa: BLE001
        rec.update(status="FAILED", finished_at=datetime.now(timezone.utc).isoformat(), result={"error": str(exc)})
        logger.error("[Do] ✗ %s FAILED – %s", do_id, exc)

    _upsert(rec)

# ────────────────────────────────
# Celery 有り: 本物の Task
# ────────────────────────────────
if _HAS_CELERY:  # pragma: no cover
    @shared_task(
        bind=True,
        name="core.tasks.do_tasks.run_do_task",
        acks_late=True,
        max_retries=3,
    )
    def run_do_task(self: Task, do_id: str, plan_id: str, params: dict) -> None:  # type: ignore[override]
        try:
            _execute(do_id, plan_id, params)
        except Exception as exc:  # noqa: BLE001
            raise self.retry(exc=exc, countdown=min(300, 30 * (self.request.retries + 1)))

# ────────────────────────────────
# Celery 無し: 同期実行シェル
# ────────────────────────────────
else:
    class _SyncAsyncResult:
        def __init__(self, task_id: str):
            self.id = task_id
        @property
        def state(self) -> str:
            return "SUCCESS"

    class _SyncTask:  # Celery 互換
        @staticmethod
        def apply_async(
            args: list | tuple,
            kwargs: dict | None = None,
            task_id: str | None = None,
            **__,
        ) -> _SyncAsyncResult:
            do_id, plan_id, params = args
            _execute(do_id, plan_id, params)
            return _SyncAsyncResult(task_id or uuid.uuid4().hex)

    run_do_task = _SyncTask()  # type: ignore[assignment]

__all__ = ["run_do_task"]