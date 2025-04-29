# =====================================================================
# ASSIST_KEY: 【api/routers/do_api.py】
# =====================================================================
#
# DoRouter ― “Do フェーズ” をバックグラウンド実行する REST ルータ
# ---------------------------------------------------------------------

from __future__ import annotations

import logging
import uuid
from typing import List, Optional, Any, Dict

from fastapi import APIRouter, BackgroundTasks, HTTPException, status

from core.do.coredo_executor import run_do
from core.schemas.do_schemas import DoCreateRequest, DoResponse
from core.schemas.plan_schemas import PlanResponse
from core.repository.factory import get_repo

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/do", tags=["do"])

# ---------------------------------------------------------------------
# Repository (DB_BACKEND に応じて memory / sqlite / postgres を自動選択)
# ---------------------------------------------------------------------
_do_repo   = get_repo(table="do")
_plan_repo = get_repo(table="plan")

# =====================================================================
# POST /do/{plan_id}  ― Do 実行要求
# =====================================================================
@router.post(
    "/{plan_id}",
    response_model=DoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Run Do",
)
async def create_do(                     # noqa: D401
    plan_id: str,
    bg: BackgroundTasks,
    body: Optional[DoCreateRequest] = None,
) -> DoResponse:
    """
    指定 *Plan* を **Do フェーズ** でバックグラウンド実行します。

    * 受付直後 `201 Created` を返し、実処理は別スレッドで実行  
    * 1 Plan ≫ n Do を許容（`do-xxxxxxxx` を毎回採番）  
    * 進捗は `status=PENDING|RUNNING|DONE|FAILED` で追跡
    """
    # ---------- Plan 存在チェック ----------
    plan_rec: Dict[str, Any] | None = _plan_repo.get(plan_id)
    if plan_rec is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan '{plan_id}' not found",
        )

    body = body or DoCreateRequest()

    # ---------- run_no / seq 補完 ----------
    run_no = body.run_no or body.seq or 1
    body.run_no = run_no            # executor 用
    body.seq    = run_no            # レスポンス用

    # ---------- 初期レコード ----------
    do_id  = f"do-{uuid.uuid4().hex[:8]}"
    record = {
        "do_id":   do_id,
        "plan_id": plan_id,
        "seq":     run_no,
        "run_tag": body.run_tag,
        "status":  "PENDING",
        "result":  None,
        "dashboard_url": None,
    }
    _do_repo.create(do_id, record)

    # ---------- BG 実行 ----------
    bg.add_task(
        _execute_do_sync,
        do_id,
        PlanResponse(**plan_rec),
        body,
    )

    return DoResponse(**record)


# =====================================================================
# GET /do/{do_id} ― 単一取得
# =====================================================================
@router.get(
    "/{do_id}",
    response_model=DoResponse,
    summary="Get Do",
)
async def get_do(do_id: str) -> DoResponse:
    rec = _do_repo.get(do_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="Do not found")
    return DoResponse(**rec)


# =====================================================================
# GET /do/ ― 一覧取得
# =====================================================================
@router.get(
    "/",
    response_model=List[DoResponse],
    summary="List Do",
)
async def list_do() -> List[DoResponse]:
    return [DoResponse(**r) for r in _do_repo.list()]


# ---------------------------------------------------------------------
# 内部処理
# ---------------------------------------------------------------------
def _execute_do_sync(
    do_id: str,
    plan: PlanResponse,
    req: DoCreateRequest,
) -> None:
    """
    同期 `run_do()` を呼び出し、状態遷移を
      RUNNING → DONE / FAILED
    として _do_repo に保存する。
    """

    def _save(state: dict) -> None:
        # シンプルな upsert (delete→create) でバックエンド差異を吸収
        _do_repo.delete(do_id)
        _do_repo.create(do_id, state)

    # ---------------------------- RUNNING ----------------------------
    rec = _do_repo.get(do_id) or {}
    rec["status"] = "RUNNING"
    _save(rec)

    # ---------------------- パラメータ統合 ---------------------------
    merged_params: dict[str, Any] = {
        # Plan がデフォルト、Do リクエストが優先
        "symbol":     req.symbol or plan.symbol,
        "start":      req.start  or plan.start.isoformat(),
        "end":        req.end    or plan.end.isoformat(),
        "indicators": req.indicators or [],
        "run_no":     req.run_no,
    }

    try:
        # ★ run_do(plan_id, params-dict) に合わせて呼び出し ★
        result = run_do(plan.id, merged_params)

        rec.update(status="DONE", result=result)
        _save(rec)
        logger.info("[Do] ✓ %s DONE", do_id)

    except Exception as exc:                # noqa: BLE001
        rec.update(status="FAILED", result={"error": str(exc)})
        _save(rec)
        logger.error("[Do] ✗ %s FAILED – %s", do_id, exc)
