# ─── api/routers/do_api.py ──────────────────────────────────────────────
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, cast

from celery import states
from celery.backends.base import DisabledBackend
from celery.result import AsyncResult
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from core.celery_app import celery_app
from core.repository.factory import get_repo
from core.schemas.do_schemas import DoCreateRequest, DoResponse, DoStatus
from core.schemas.plan_schemas import PlanResponse
from core.tasks.do_tasks import run_do_task  # Celery タスク

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/do", tags=["do"])

_plan_repo = get_repo("plan")
_do_repo = get_repo("do")


# --------------------------------------------------------------------- #
# 内部ユーティリティ
# --------------------------------------------------------------------- #
def _merge_params(plan: PlanResponse, req: DoCreateRequest) -> Dict[str, Any]:
    """
    Plan とリクエストをマージして Do タスク用パラメータ dict を返す。
    start / end が両方とも欠落している場合は 400 を返す。
    """
    start_dt = req.start or plan.start
    end_dt = req.end or plan.end

    if start_dt is None or end_dt is None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="start / end datetime が Plan とリクエストの両方で欠落しています",
        )

    params: Dict[str, Any] = {
        "symbol": req.symbol or plan.symbol,
        "start": start_dt.isoformat(),
        "end": end_dt.isoformat(),
        "indicators": req.indicators or [],
        "run_no": req.run_no,
        "run_tag": req.run_tag,
    }

    # symbol が空なら Plan.data.universe[0] を採用
    if not params["symbol"]:
        universe = getattr(plan, "data", {}).get("universe", [])
        if isinstance(universe, list) and universe:
            params["symbol"] = str(universe[0])
        else:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="symbol is required either in Plan or in DoCreateRequest",
            )
    return params


def _upsert(rec: Dict[str, Any]) -> None:
    """delete→create ではなく既存値をマージして保存する。"""
    do_id = rec["do_id"]
    current = _do_repo.get(do_id) or {}
    current.update(rec)
    try:
        _do_repo.delete(do_id)
    except Exception:
        pass
    _do_repo.create(do_id, current)


# --------------------------------------------------------------------- #
# エンドポイント
# --------------------------------------------------------------------- #
@router.post(
    "/{plan_id}",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Enqueue Do job (Celery)",
    response_model=Dict[str, str],
)
def enqueue_do(plan_id: str, body: Optional[DoCreateRequest] = None) -> JSONResponse:
    # 1) Plan 存在チェック
    plan_raw = _plan_repo.get(plan_id)
    if plan_raw is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"Plan '{plan_id}' not found")
    plan = PlanResponse(**plan_raw)

    # 2) リクエスト補完
    # ★ Pydantic v1 互換として construct() を fallback
    if body is not None:
        req = body
    else:
        construct = getattr(DoCreateRequest, "model_construct", None)
        if construct is None:
            construct = DoCreateRequest.construct  # type: ignore[attr-defined]
        req = construct()  # type: ignore[call-arg]
    req.run_no = req.run_no or req.seq or 1
    req.seq = req.run_no

    # 3) ID 発行
    task_id = uuid.uuid4().hex
    do_id = f"do-{task_id[:8]}"

    # 4) パラメータマージ
    params = _merge_params(plan, req)

    # 5) 初期レコード保存
    now = datetime.now(timezone.utc).isoformat()
    _upsert(
        {
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
    )

    # 6) Celery 実行
    if celery_app.conf.task_always_eager:
        run_do_task(do_id, plan_id, params)  # 同期
    else:
        # ★ apply_async の args 型は Tuple[Any, ...] と明示
        run_do_task.apply_async(
            args=cast(Tuple[Any, ...], (do_id, plan_id, params)), task_id=task_id
        )

    return JSONResponse(status_code=status.HTTP_202_ACCEPTED, content={"do_id": do_id, "task_id": task_id})


@router.get("/{do_id}", response_model=DoResponse, summary="Get Do record")
def get_do(do_id: str) -> DoResponse:
    rec = _do_repo.get(do_id)
    if rec is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"Do '{do_id}' not found")
    return DoResponse(**rec)


@router.get("/status/{task_id}", response_model=Dict[str, Any], summary="Raw Celery task state")
def get_do_status(task_id: str) -> Dict[str, Any]:
    """Celery backend が DisabledBackend の場合は SUCCESS 扱いにフォールバック。"""
    result = AsyncResult(task_id)
    try:
        state = result.state
        payload: Dict[str, Any] = {"state": state}
        if state == states.FAILURE and result.result:
            payload["error"] = str(result.result)
        else:
            payload["result"] = result.result  # type: ignore[assignment]
    except AttributeError:
        payload = {"state": states.SUCCESS}
    except Exception as exc:  # DisabledBackend は Exception を継承しない
        if isinstance(exc, DisabledBackend):
            payload = {"state": states.SUCCESS}
        else:
            raise
    return payload


@router.get("/", response_model=List[DoResponse], summary="List Do records")
def list_do() -> List[DoResponse]:
    return [DoResponse(**v) for v in _do_repo.list()]
