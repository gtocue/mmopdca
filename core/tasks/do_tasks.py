# =====================================================================
# ASSIST_KEY: 【core/tasks/do_tasks.py】 – Celery Task Entrypoint
# =====================================================================
#
# “Do フェーズ” をバックグラウンドで実行する Celery / Sync タスク。
#   • args = (do_id, plan_id, params)  ← ← ★ ココが標準
#   • 成功時は metrics_repo にも push
# ---------------------------------------------------------------------
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict

from core.repository.factory import get_repo
from core.do.coredo_executor import run_do
from core.schemas.do_schemas import DoStatus

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------ #
# Repositories
# ------------------------------------------------------------------ #
_do_repo      = get_repo("do")
_metrics_repo = get_repo("metrics")

def _upsert(rec: Dict[str, Any]) -> None:
    _do_repo.upsert(rec["do_id"], rec)

# ------------------------------------------------------------------ #
# 実行本体
# ------------------------------------------------------------------ #
def _execute(do_id: str, plan_id: str, params: Dict[str, Any]) -> None:
    rec = _do_repo.get(do_id) or {}
    rec.update(status=DoStatus.RUNNING, started_at=datetime.now(timezone.utc).isoformat())
    _upsert(rec)

    try:
        result  = run_do(plan_id, params)
        metrics = result.get("metrics") or {}
        if metrics:
            _metrics_repo.put(do_id, metrics)

        rec.update(
            status       = DoStatus.DONE,
            finished_at  = datetime.now(timezone.utc).isoformat(),
            result       = result,
            artifact_uri = result.get("artifact_uri"),
        )
        logger.info("[Do] ✓ %s DONE", do_id)
    except Exception as exc:  # noqa: BLE001
        rec.update(
            status       = DoStatus.FAILED,
            finished_at  = datetime.now(timezone.utc).isoformat(),
            result       = {"error": str(exc)},
        )
        logger.error("[Do] ✗ %s FAILED – %s", do_id, exc)

    _upsert(rec)

# ------------------------------------------------------------------ #
# Celery or Sync?
# ------------------------------------------------------------------ #
try:
    from celery import shared_task, Task  # type: ignore
    _HAS_CELERY = True
except ModuleNotFoundError:  # pragma: no cover
    _HAS_CELERY = False

if _HAS_CELERY:                      # ───── Celery 版 ─────
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
else:                                # ───── フォールバック ─────
    class _SyncAsyncResult:
        def __init__(self, task_id: str):
            self.id = task_id
        @property
        def state(self) -> str:  # noqa: D401
            return "SUCCESS"

    class _SyncTask:
        @staticmethod
        def apply_async(
            args: list | tuple,
            kwargs: dict | None = None,
            task_id: str | None = None,
            **__,
        ) -> _SyncAsyncResult:
            _execute(*args)
            return _SyncAsyncResult(task_id or "sync-mode")

    run_do_task = _SyncTask()  # type: ignore[assignment]

__all__ = ["run_do_task"]
