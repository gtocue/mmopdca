# =========================================================
# ASSIST_KEY: このファイルは【api/routers/do_api.py】に位置するユニットです
# =========================================================
#
# Do-phase Router – Celery 完全オフロード
#   • POST  /do/{plan_id}        : 202 Accepted で {do_id, task_id}
#   • GET   /do/{do_id}          : 実行状態／結果 (DoResponse)
#   • GET   /do/                 : 一覧
#   • GET   /do/status/{task_id} : Celery タスク state
# ---------------------------------------------------------
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

from core.celery_app import run_do_task           # Celery タスク
from core.repository.factory import get_repo
from core.schemas.do_schemas import DoCreateRequest, DoResponse, DoStatus
from core.schemas.plan_schemas import PlanResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/do", tags=["do"])

_plan_repo = get_repo("plan")
_do_repo   = get_repo("do")

# ------------------------------------------------------------------ #
# helpers
# ------------------------------------------------------------------ #
def _merge_params(plan: PlanResponse, req: DoCreateRequest) -> Dict[str, Any]:
    params: Dict[str, Any] = {
        "symbol": req.symbol or plan.symbol,
        "start": (req.start or plan.start).isoformat(),
        "end":   (req.end or plan.end).isoformat(),
        "indicators": req.indicators or [],
        "run_no": req.run_no,
        "run_tag": req.run_tag,
    }
    # Plan.data.universe 補完
    if not params["symbol"]:
        universe = getattr(plan, "data", {}).get("universe", [])  # type: ignore[attr-defined]
        if isinstance(universe, list) and universe:
            params["symbol"] = str(universe[0])
        else:
            raise HTTPException(400, detail="symbol is required")
    return params


def _upsert(rec: Dict[str, Any]) -> None:
    _do_repo.upsert(rec["do_id"], rec)

# ------------------------------------------------------------------ #
# POST /do/{plan_id}
# ------------------------------------------------------------------ #
@router.post(
    "/{plan_id}",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Enqueue Do job (Celery)",
)
def enqueue_do(plan_id: str, body: Optional[DoCreateRequest] = None) -> JSONResponse:
    # --- Plan 取得 ---------------------------------------------------
    plan_raw = _plan_repo.get(plan_id)
    if plan_raw is None:
        raise HTTPException(404, detail=f"Plan '{plan_id}' not found")
    plan = PlanResponse(**plan_raw)

    # --- リクエスト正規化 -------------------------------------------
    req = body or DoCreateRequest()
    run_no = req.run_no or req.seq or 1
    req.run_no = req.seq = run_no

    # --- ID 生成 -----------------------------------------------------
    task_id = uuid.uuid4().hex
    do_id   = f"do-{task_id[:8]}"        # ★ Celery 引数に必要なので先に作成

    # --- Celery 発火 --------------------------------------------------
    run_do_task.apply_async(             # ★ 引数は 3 つ
        args=[do_id, plan.id, _merge_params(plan, req)],
        task_id=task_id,
    )

    # --- 初期レコード保存 -------------------------------------------
    _do_repo.create(
        do_id,
        {
            "do_id": do_id,
            "plan_id": plan_id,
            "seq": run_no,
            "run_tag": req.run_tag,
            "status": DoStatus.PENDING,
            "result": None,
            "artifact_uri": None,
            "dashboard_url": None,
            "celery_task_id": task_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
    )

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
        raise HTTPException(404, "Do job not found")

    # --- DONE / FAILED はそのまま返す -------------------------------
    if rec["status"] in {DoStatus.DONE, DoStatus.FAILED}:
        return DoResponse(**rec)

    # --- Celery Task 状態を取得 -------------------------------------
    task = AsyncResult(rec["celery_task_id"])

    # backend 無効の場合は状態を推測だけ更新
    if isinstance(task.backend, DisabledBackend):
        if rec["status"] == DoStatus.PENDING:
            rec["status"] = DoStatus.RUNNING
            _upsert(rec)
        return DoResponse(**rec)

    # backend 有効 : 正確に同期
    try:
        state = task.state
    except Exception as exc:  # pragma: no cover
        logger.warning("[Do] backend error: %s", exc)
        return DoResponse(**rec)

    if state == states.SUCCESS:
        result: Dict[str, Any] = task.result or {}
        rec.update(
            status=DoStatus.DONE,
            result=result,
            artifact_uri=result.get("artifact_uri"),
        )
    elif state == states.FAILURE:
        rec.update(
            status=DoStatus.FAILED,
            result={"error": str(task.result)},
        )
    elif state in {states.STARTED, states.RETRY}:
        rec["status"] = DoStatus.RUNNING

    _upsert(rec)
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
