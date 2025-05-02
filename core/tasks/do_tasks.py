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

# ------------------------------------------------------------------ #
# Repository (plan / do) – メモリ・SQLite・Postgres 等を自動選択
# ------------------------------------------------------------------ #
_plan_repo = get_repo(table="plan")
_do_repo   = get_repo(table="do")
_loader    = PlanLoader(validate=False)

# ===================================================================
# Celery が使えるかどうか判定
# ===================================================================
try:
    from celery import shared_task, Task  # type: ignore
    _HAS_CELERY = True
except ModuleNotFoundError:               # pragma: no cover
    _HAS_CELERY = False
    shared_task = None        # type: ignore
    Task = object             # type: ignore

# -------------------------------------------------------------------
# 共通ヘルパ
# -------------------------------------------------------------------
def _upsert(record: Dict[str, Any]) -> None:
    """Memory/Redis 系で update が無いケースを考慮して upsert."""
    _do_repo.delete(record["do_id"])
    _do_repo.create(record["do_id"], record)


def _execute(do_id: str, plan_id: str, params: Dict[str, Any]) -> None:
    """実際に run_do() を叩き、結果をレポジトリへ反映。"""
    rec = _do_repo.get(do_id) or {}
    rec["status"] = "RUNNING"
    _upsert(rec)

    try:
        result = run_do(plan_id, params)
        rec.update(status="DONE", result=result)
        logger.info("[Do] ✓ %s DONE", do_id)
    except Exception as exc:  # noqa: BLE001
        rec.update(status="FAILED", result={"error": str(exc)})
        logger.error("[Do] ✗ %s FAILED – %s", do_id, exc)

    _upsert(rec)

# ===================================================================
# Celery あり: 本物の Task
# ===================================================================
if _HAS_CELERY:  # pragma: no cover – CI ではスキップ
    @shared_task(bind=True, name="run_do_task", acks_late=True, max_retries=3)
    def run_do_task(self: Task, do_id: str, plan_id: str, params: dict) -> None:  # type: ignore[override]
        """
        本番用 Celery タスク。失敗時は指数バックオフで自動再試行。
        """
        try:
            _execute(do_id, plan_id, params)
        except Exception as exc:                                              # noqa: BLE001
            # 失敗したら Celery のリトライ機構に任せる
            raise self.retry(exc=exc, countdown=min(300, 30 * (self.request.retries + 1)))

# ===================================================================
# Celery なし: ダミー Task（同期実行）  ※テスト/ローカル用
# ===================================================================
else:
    class _SyncAsyncResult:  # 最低限の擬似 AsyncResult
        id: str
        def __init__(self, task_id: str): self.id = task_id
        @property
        def state(self) -> str: return "SUCCESS"

    class _SyncTask:  # Celery 互換シェル
        @staticmethod
        def apply_async(args: list | tuple, kwargs: dict | None = None, task_id: str | None = None, **__) -> _SyncAsyncResult:  # noqa: D401
            """Celery が無い場合でも呼び出せるダミー enqueue。"""
            do_id, plan_id, params = args
            _execute(do_id, plan_id, params)
            return _SyncAsyncResult(task_id or uuid.uuid4().hex)

    # 呼び出し側からは同じ名前で見えるようエクスポート
    run_do_task = _SyncTask()  # type: ignore[assignment]

# -------------------------------------------------------------------
# public re-export
# -------------------------------------------------------------------
__all__ = ["run_do_task"]
