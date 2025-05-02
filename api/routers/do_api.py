# ======================================================================
# api/routers/do_api.py
# ----------------------------------------------------------------------
#   Do-phase Router  ―  Celery へ完全オフロード（HTTP 202 Accepted）
#
#   • POST  /do/{plan_id}        : すぐに 202 + {do_id, task_id}
#   • GET   /do/{do_id}          : 実行状態 / 結果
#   • GET   /do/                 : 一覧
#   • GET   /do/status/{task_id} : Celery Task の state だけ返す
# ======================================================================

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from celery import states
from celery.backends.base import DisabledBackend
from celery.result import AsyncResult
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from core.celery_app import run_do_task          # Celery タスク
from core.repository.factory import get_repo
from core.schemas.do_schemas import DoCreateRequest, DoResponse
from core.schemas.plan_schemas import PlanResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/do", tags=["do"])

_plan_repo = get_repo(table="plan")
_do_repo   = get_repo(table="do")

# ------------------------------------------------------------------ #
# helpers
# ------------------------------------------------------------------ #
def _merge_params(plan: PlanResponse, req: DoCreateRequest) -> Dict[str, Any]:
    """Plan とリクエスト Body をマージして Executor 用 param dict を作る。"""
    params: Dict[str, Any] = {
        "symbol":     req.symbol or plan.symbol,
        "start":      req.start  or plan.start.isoformat(),
        "end":        req.end    or plan.end.isoformat(),
        "indicators": req.indicators or [],
        "run_no":     req.run_no,
    }
    if not params["symbol"]:
        universe = getattr(plan, "data", {}).get("universe", [])  # type: ignore[attr-defined]
        if isinstance(universe, list) and universe:
            params["symbol"] = str(universe[0])
        else:
            raise HTTPException(400, detail="symbol is required")
    return params


def _upsert_do(rec: Dict[str, Any]) -> None:
    """MemoryRepository 等に合わせて簡易 upsert を実施。"""
    _do_repo.delete(rec["do_id"])
    _do_repo.create(rec["do_id"], rec)

# ------------------------------------------------------------------ #
# POST /do/{plan_id}
# ------------------------------------------------------------------ #
@router.post(
    "/{plan_id}",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Enqueue Do job (Celery)",
)
def enqueue_do(
    plan_id: str,
    body: Optional[DoCreateRequest] = None,
) -> JSONResponse:
    """Do ジョブを Celery へ投入し、即 202 Accepted を返す。"""
    # 1) Plan 存在チェック
    plan_raw = _plan_repo.get(plan_id)
    if plan_raw is None:
        raise HTTPException(404, detail=f"Plan '{plan_id}' not found")
    plan = PlanResponse(**plan_raw)

    req    = body or DoCreateRequest()
    run_no = req.run_no or req.seq or 1
    req.run_no = req.seq = run_no

    # 2) Celery publish
    task_id = uuid.uuid4().hex
    run_do_task.apply_async(
        args=[plan.id, _merge_params(plan, req)],
        task_id=task_id,
    )

    # 3) Do レコード初期化
    do_id = f"do-{task_id[:8]}"
    rec   = {
        "do_id":          do_id,
        "plan_id":        plan_id,
        "seq":            run_no,
        "run_tag":        req.run_tag,
        "status":         "PENDING",
        "result":         None,
        "dashboard_url":  None,
        "celery_task_id": task_id,
        "created_at":     datetime.now(timezone.utc).isoformat(),
    }
    _do_repo.create(do_id, rec)

    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content={"do_id": do_id, "task_id": task_id},
    )

# ------------------------------------------------------------------ #
# GET /do/{do_id}
# ------------------------------------------------------------------ #
@router.get("/{do_id}", response_model=DoResponse, summary="Get Do job")
def get_do(do_id: str) -> DoResponse:
    rec = _do_repo.get(do_id)
    if rec is None:
        raise HTTPException(404, detail="Do job not found")

    # 既に DONE / FAILED ならそのまま返す
    if rec["status"] in {"DONE", "FAILED"}:
        return DoResponse(**rec)

    task = AsyncResult(rec["celery_task_id"])

    # Result backend が無効（redis 未接続など）の場合
    if isinstance(task.backend, DisabledBackend):
        if task.state in {states.STARTED, states.RETRY} and rec["status"] == "PENDING":
            rec["status"] = "RUNNING"
            _upsert_do(rec)
        return DoResponse(**rec)

    # backend 有効時のみ最終結果を同期反映
    if task.state == states.SUCCESS:
        rec.update(status="DONE", result=task.result)
        _upsert_do(rec)
    elif task.state == states.FAILURE:
        rec.update(status="FAILED", result={"error": str(task.result)})
        _upsert_do(rec)
    elif task.state in {states.STARTED, states.RETRY}:
        rec["status"] = "RUNNING"
        _upsert_do(rec)

    return DoResponse(**rec)

# ------------------------------------------------------------------ #
# GET /do/status/{task_id}
# ------------------------------------------------------------------ #
@router.get("/status/{task_id}", summary="Get Celery task state")
def get_task_state(task_id: str) -> Dict[str, str]:
    return {"state": AsyncResult(task_id).state}

# ------------------------------------------------------------------ #
# GET /do/
# ------------------------------------------------------------------ #
@router.get("/", response_model=List[DoResponse], summary="List Do jobs")
def list_do() -> List[DoResponse]:
    return [DoResponse(**r) for r in _do_repo.list()]
