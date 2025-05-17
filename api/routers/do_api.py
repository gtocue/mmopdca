# File: api/routers/do_api.py
# Name: Do-phase Router
# Summary: Do フェーズのキューイングとステータス照会を提供する FastAPI ルータ

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
from core.tasks.do_tasks import run_do_task  # Celery タスク

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/do", tags=["do"])

# リポジトリ取得
_plan_repo = get_repo("plan")
_do_repo = get_repo("do")


def _merge_params(plan: PlanResponse, req: DoCreateRequest) -> Dict[str, Any]:
    """
    Plan とリクエスト内容を合わせて、実際の run_do_task に渡すパラメータ辞書を構築。
    """
    params: Dict[str, Any] = {
        "symbol": req.symbol or plan.symbol,
        "start": (req.start or plan.start).isoformat(),
        "end": (req.end or plan.end).isoformat(),
        "indicators": req.indicators or [],
        "run_no": req.run_no,
        "run_tag": req.run_tag,
    }
    if not params["symbol"]:
        univ = getattr(plan, "data", {}).get("universe", [])
        if isinstance(univ, list) and univ:
            params["symbol"] = str(univ[0])
        else:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="symbol is required either in Plan or in DoCreateRequest",
            )
    return params


def _upsert(rec: Dict[str, Any]) -> None:
    """
    同一 do_id があればいったん消してから再作成し、upsert を実現。
    """
    try:
        _do_repo.delete(rec["do_id"])
    except Exception:
        pass
    _do_repo.create(rec["do_id"], rec)


@router.post(
    "/{plan_id}",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Enqueue Do job (Celery)",
    response_model=Dict[str, str],
)
def enqueue_do(plan_id: str, body: Optional[DoCreateRequest] = None) -> JSONResponse:
    """
    Plan に紐づく Do フェーズのジョブを Celery に enqueue（または同期実行）する。
    """
    # 1) Plan の存在チェック
    plan_raw = _plan_repo.get(plan_id)
    if plan_raw is None:
        logger.error("Plan '%s' not found", plan_id)
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail=f"Plan '{plan_id}' not found"
        )
    plan = PlanResponse(**plan_raw)

    # 2) リクエストボディを標準化
    req = body or DoCreateRequest()
    req.run_no = req.run_no or req.seq or 1
    req.seq = req.run_no

    # 3) do_id／task_id を生成
    task_id = uuid.uuid4().hex
    do_id = f"do-{task_id[:8]}"

    # 4) 実行パラメータをマージ
    params = _merge_params(plan, req)

    # 5) **初期ステータスを永続化**（同期実行でもここで一度 PENDING を保存）
    now = datetime.now(timezone.utc).isoformat()
    initial_rec: Dict[str, Any] = {
        "do_id": do_id,
        "plan_id": plan_id,
        "seq": req.run_no,
        "run_tag": req.run_tag,
        "status": DoStatus.PENDING,
        "result": None,
        "artifact_uri": None,
        "dashboard_url": None,
        "celery_task_id": task_id,
        "created_at": now,
        "updated_at": None,
        "completed_at": None,
    }
    _upsert(initial_rec)

    # 6) Celery タスクを実行（Eager モード時は同期、通常はキュー登録）
    if celery_app.conf.task_always_eager:
        # 同期実行
        run_do_task(do_id, plan_id, params)
    else:
        # 非同期キュー登録
        run_do_task.apply_async(args=(do_id, plan_id, params), task_id=task_id)

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
    """
    do_id で指定した Do レコードを返す。
    """
    rec = _do_repo.get(do_id)
    if rec is None:
        logger.error("Do '%s' not found", do_id)
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"Do '{do_id}' not found")
    return DoResponse(**rec)


@router.get(
    "/status/{task_id}",
    summary="Raw Celery task state",
    response_model=Dict[str, Any],
)
def get_do_status(task_id: str) -> Dict[str, Any]:
    """
    Celery の AsyncResult を使って、タスクの生の状態を返す。
    """
    res = AsyncResult(task_id)
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
    """
    保存済みの全 Do レコード一覧を返す。
    """
    return [DoResponse(**v) for v in _do_repo.list()]
