# =========================================================
# ASSIST_KEY: 【api/routers/check_api.py】 – Check-phase Router
# =========================================================
#
# 【概要】
#   • POST  /check/{do_id}        → Celery に enqueue（202 Accepted） & 初期レコード作成
#   • GET   /check/{check_id}     → 永続化されたチェック結果を取得
#   • GET   /check/status/{task_id} → Celery Task の生ステータス取得
#   • GET   /check/               → 全チェックレコード一覧取得
#
# 【主な役割】
#   - タスク発行時のレコード生成
#   - Celery タスクの enqueue (run_check_task)
#   - レコード取得・リスト化
#
# 【依存関係】
#   - core.celery_app.celery_app
#   - core.tasks.check_tasks.run_check_task
#   - core.repository.factory.get_repo
#   - core.schemas.check_schemas.CheckResult
#
# 【ルール遵守】
#   1) created_at は UTC ISO8601 形式
#   2) upsert は delete()+create() の組合せ
#   3) Pydantic v2 モデルとのフィールド整合性保持
# ---------------------------------------------------------
from __future__ import annotations
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from celery import states
from celery.backends.base import DisabledBackend
from celery.result import AsyncResult

from core.celery_app import celery_app
from core.repository.factory import get_repo
from core.schemas.check_schemas import CheckResult

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/check", tags=["check"])

_check_repo = get_repo("check")
_do_repo    = get_repo("do")


def _upsert(rec: Dict[str, Any]) -> None:
    """同一IDのレコードを削除してから作成し、upsert を実現"""
    try:
        _check_repo.delete(rec["id"])
    except Exception:
        pass
    _check_repo.create(rec["id"], rec)


@router.post(
    "/{do_id}",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Enqueue Check job (Celery)",
)
def enqueue_check(do_id: str) -> JSONResponse:
    """Check フェーズのタスクを Celery に登録 & 初期レコードを作成"""
    # Do が存在することを確認
    if _do_repo.get(do_id) is None:
        logger.error("Do '%s' not found", do_id)
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"Do '{do_id}' not found")

    # task_id / check_id 生成
    task_id  = uuid.uuid4().hex
    check_id = f"check-{task_id[:8]}"

    # Celery に enqueue (文字列タスク名)
    celery_app.send_task(
        "core.tasks.check_tasks.run_check_task",
        args=[check_id, do_id],
        task_id=task_id,
    )

    # 初期レコード作成
    rec: Dict[str, Any] = {
        "id": check_id,
        "do_id": do_id,
        "status": "PENDING",
        "report": None,
        "celery_task_id": task_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    _upsert(rec)

    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content={"id": check_id, "task_id": task_id},
    )


@router.get(
    "/{check_id}",
    response_model=CheckResult,
    summary="Get Check record",
)
def get_check(check_id: str) -> CheckResult:
    """永続化されたチェックレコードを返却"""
    rec = _check_repo.get(check_id)
    if rec is None:
        logger.error("Check '%s' not found", check_id)
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"Check '{check_id}' not found")
    return CheckResult(**rec)


@router.get(
    "/status/{task_id}",
    summary="Raw Celery task state",
)
def get_check_status(task_id: str) -> Dict[str, Any]:
    """Celery タスクの生ステータスおよびエラーを取得"""
    res   = AsyncResult(task_id)
    state = res.state
    payload: Dict[str, Any] = {"state": state}
    if state == states.FAILURE and res.result:
        payload["error"] = str(res.result)
    try:
        payload["result"] = res.result  # type: ignore
    except DisabledBackend:
        pass
    return payload


@router.get(
    "/",
    response_model=List[CheckResult],
    summary="List Check records",
)
def list_check() -> List[CheckResult]:
    """保存済みの Check レコードをすべて返却"""
    return [CheckResult(**rec) for rec in _check_repo.list()]