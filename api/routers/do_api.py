# =========================================================
# ASSIST_KEY: 【api/routers/do_api.py】  – Do-phase Router
# =========================================================
#
#  • POST  /do/{plan_id}        → Celery に enqueue（202 Accepted）
#  • GET   /do/{do_id}          → 進捗 / 結果を返す
#  • GET   /do/status/{task_id} → Celery Task の生 State
#  • GET   /do/                 → 一覧
# ---------------------------------------------------------
from __future__ import annotations
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from celery import states
from celery.backends.base import DisabledBackend
from celery.result import AsyncResult

from core.celery_app import celery_app
from core.repository.factory import get_repo
from core.schemas.plan_schemas import PlanResponse
from core.schemas.do_schemas import DoCreateRequest, DoResponse, DoStatus

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/do", tags=["do"])

_plan_repo = get_repo("plan")
_do_repo   = get_repo("do")


def _merge_params(plan: PlanResponse, req: DoCreateRequest) -> Dict[str, Any]:
    """Plan とリクエストをマージして最終パラメータ辞書を作る。"""
    params: Dict[str, Any] = {
        "symbol":     req.symbol     or plan.symbol,
        "start":      (req.start     or plan.start).isoformat(),
        "end":        (req.end       or plan.end).isoformat(),
        "indicators": req.indicators or [],
        "run_no":     req.run_no,
        "run_tag":    req.run_tag,
    }
    if not params["symbol"]:
        univ = getattr(plan, "data", {}).get("universe", [])
        if isinstance(univ, list) and univ:
            params["symbol"] = str(univ[0])
        else:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="symbol is required")
    return params


def _upsert(rec: Dict[str, Any]) -> None:
    """同一ID があれば削除してから作成して upsert を実現。"""
    try:
        _do_repo.delete(rec["do_id"])
    except Exception:
        pass
    _do_repo.create(rec["do_id"], rec)


@router.post(
    "/{plan_id}",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Enqueue Do job (Celery)",
)
def enqueue_do(plan_id: str, body: Optional[DoCreateRequest] = None) -> JSONResponse:
    """Do フェーズを非同期実行するタスクをキューに登録する。"""
    # 1) Plan を取得
    plan_raw = _plan_repo.get(plan_id)
    if plan_raw is None:
        logger.error("Plan '%s' not found", plan_id)
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"Plan '{plan_id}' not found")
    plan = PlanResponse(**plan_raw)

    # 2) リクエスト正規化
    req = body or DoCreateRequest()
    req.run_no = req.run_no or req.seq or 1
    req.seq    = req.run_no

    # 3) 一意な ID を生成
    task_id = uuid.uuid4().hex
    do_id   = f"do-{task_id[:8]}"

    # 4) パラメータマージ
    params = _merge_params(plan, req)

    # 5) Celery へ enqueue (文字列タスク名)
    celery_app.send_task(
        "core.tasks.do_tasks.run_do_task",
        args=[do_id, plan_id, params],
        task_id=task_id,
    )

    # 6) 初期レコード保存
    rec: Dict[str, Any] = {
        "do_id":          do_id,
        "plan_id":        plan_id,
        "seq":            req.run_no,
        "run_tag":        req.run_tag,
        "status":         DoStatus.PENDING,
        "result":         None,
        "artifact_uri":   None,
        "dashboard_url":  None,
        "celery_task_id": task_id,
        "created_at":     datetime.now(timezone.utc).isoformat(),
    }
    _upsert(rec)

    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content={"do_id": do_id, "task_id": task_id},
    )


@router.get(
    "/{do_id}",
    response_model=DoResponse,
    summary="Get Do record",
)
def get_do(do_id: str) -> DoResponse:
    rec = _do_repo.get(do_id)
    if rec is None:
        logger.error("Do '%s' not found", do_id)
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"Do '{do_id}' not found")
    return DoResponse(**rec)


@router.get(
    "/status/{task_id}",
    summary="Raw Celery task state",
)
def get_do_status(task_id: str) -> Dict[str, Any]:
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
    response_model=List[DoResponse],
    summary="List Do records",
)
def list_do() -> List[DoResponse]:
    """保存済み Do レコードをすべて返す。"""
    return [DoResponse(**v) for v in _do_repo.list()]