# =========================================================
# api/routers/check_api.py – Check-phase Router  (Fixed)
# =========================================================
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

from celery import states
from celery.backends.base import DisabledBackend
from celery.result import AsyncResult
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from core.celery_app import celery_app
from core.repository.factory import get_repo
from core.schemas.check_schemas import CheckResult

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/check", tags=["check"])

_check_repo = get_repo("check")
_do_repo = get_repo("do")


# --------------------------------------------------------------------- #
# 内部ユーティリティ
# --------------------------------------------------------------------- #
def _upsert(rec: Dict[str, Any]) -> None:
    """同一 ID 行を delete→create で upsert."""
    try:
        _check_repo.delete(rec["id"])
    except Exception:
        pass
    _check_repo.create(rec["id"], rec)


# --------------------------------------------------------------------- #
# エンドポイント
# --------------------------------------------------------------------- #
@router.post(
    "/{do_id}",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Enqueue Check job (Celery)",
)
def enqueue_check(do_id: str) -> JSONResponse:
    """Check フェーズの Celery タスク登録 & 初期レコード作成"""
    # Do が存在するか
    if _do_repo.get(do_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"Do '{do_id}' not found")

    task_id = uuid.uuid4().hex
    check_id = f"check-{task_id[:8]}"

    # Celery enqueue（eager モードなら同期実行）
    if celery_app.conf.task_always_eager:
        from core.tasks.check_tasks import run_check_task  # lazy
        run_check_task(check_id, do_id)
    else:
        celery_app.send_task(
            "core.tasks.check_tasks.run_check_task",
            args=[check_id, do_id],
            task_id=task_id,
        )

    # 初期レコード
    _upsert(
        {
            "id": check_id,
            "do_id": do_id,
            "status": "PENDING",
            "report": None,
            "celery_task_id": task_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
    )

    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content={"id": check_id, "task_id": task_id},
    )


@router.get("/{check_id}", response_model=CheckResult, summary="Get Check record")
def get_check(check_id: str) -> CheckResult:
    rec = _check_repo.get(check_id)
    if rec is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"Check '{check_id}' not found")
    return CheckResult(**rec)


@router.get("/status/{task_id}", summary="Raw Celery task state")
def get_check_status(task_id: str) -> Dict[str, Any]:
    """Celery タスクの生ステータス／エラーを返す"""
    res = AsyncResult(task_id)
    state = res.state
    payload: Dict[str, Any] = {"state": state}

    if state == states.FAILURE and res.result:
        payload["error"] = str(res.result)

    try:
        payload["result"] = res.result  # type: ignore
    except Exception as exc:  # DisabledBackend は Exception でない → isinstance 判定
        if not isinstance(exc, DisabledBackend):
            raise
    return payload


@router.get("/", response_model=List[CheckResult], summary="List Check records")
def list_check() -> List[CheckResult]:
    return [CheckResult(**rec) for rec in _check_repo.list()]
