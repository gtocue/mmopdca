# =====================================================================
# api/routers/do_api.py
# ---------------------------------------------------------------------
#   /do  ルータ  ―  “Do フェーズ” ジョブをバックグラウンド実行
#       • POST /do/{plan_id}   : ジョブ登録（即 201）
#       • GET  /do/{do_id}     : 単一取得
#       • GET  /do/            : 一覧取得
#
#   - Plan が無ければ 404
#   - Repository で Do レコードを CRUD
#   - 今回は Celery を経由せずスレッドプールで同期 run_do()
# =====================================================================
from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, status

from core.do.coredo_executor import run_do          # ★ 同期呼び出し
from core.repository.factory import get_repo
from core.schemas.do_schemas import DoCreateRequest, DoResponse
from core.schemas.plan_schemas import PlanResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/do", tags=["do"])

# ------------------------------------------------------------------ #
# Repository – DB_BACKEND に応じて memory / sqlite / postgres など
# ------------------------------------------------------------------ #
_do_repo   = get_repo(table="do")
_plan_repo = get_repo(table="plan")

# ================================================================== #
# POST /do/{plan_id}  ― Do 実行要求
# ================================================================== #
@router.post(
    "/{plan_id}",
    response_model=DoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Run Do job (enqueue)",
)
def enqueue_do(                             # noqa: D401
    plan_id: str,
    bg: BackgroundTasks,
    body: Optional[DoCreateRequest] = None,
) -> DoResponse:
    """Plan を Do フェーズでバックグラウンド実行（スレッドプール）。"""

    # ---------- Plan 存在確認 ----------
    plan_rec: Dict[str, Any] | None = _plan_repo.get(plan_id)
    if plan_rec is None:
        raise HTTPException(404, detail=f"Plan '{plan_id}' not found")

    plan = PlanResponse(**plan_rec)
    req  = body or DoCreateRequest()

    # ---------- run_no / seq 補完 ----------
    run_no = req.run_no or req.seq or 1
    req.run_no = run_no       # executor 用
    req.seq    = run_no       # レスポンス用

    # ---------- Do レコード初期化 ----------
    do_id  = f"do-{uuid.uuid4().hex[:8]}"
    record = {
        "do_id":         do_id,
        "plan_id":       plan_id,
        "seq":           run_no,
        "run_tag":       req.run_tag,
        "status":        "PENDING",
        "result":        None,
        "dashboard_url": None,
        "created_at":    datetime.utcnow().isoformat(),
    }
    _do_repo.create(do_id, record)

    # ---------- バックグラウンド実行 ----------
    bg.add_task(_execute_do_sync, do_id, plan, req)

    return DoResponse(**record)

# ================================================================== #
# GET /do/{do_id}
# ================================================================== #
@router.get("/{do_id}", response_model=DoResponse, summary="Get Do job")
def get_do(do_id: str) -> DoResponse:
    rec = _do_repo.get(do_id)
    if rec is None:
        raise HTTPException(404, detail="Do not found")
    return DoResponse(**rec)

# ================================================================== #
# GET /do/
# ================================================================== #
@router.get("/", response_model=List[DoResponse], summary="List Do jobs")
def list_do() -> List[DoResponse]:
    return [DoResponse(**r) for r in _do_repo.list()]

# ------------------------------------------------------------------ #
# 内部: 同期実行関数  (thread-pool 上で呼び出される)
# ------------------------------------------------------------------ #
def _execute_do_sync(
    do_id: str,
    plan: PlanResponse,
    req: DoCreateRequest,
) -> None:
    """run_do(plan_id, params_dict) を同期呼び出しして状態を更新。"""

    def _save(state: Dict[str, Any]) -> None:
        _do_repo.delete(do_id)          # upsert 簡易実装
        _do_repo.create(do_id, state)

    # ---------------------------- RUNNING ----------------------------
    rec = _do_repo.get(do_id) or {}
    rec["status"] = "RUNNING"
    _save(rec)

    # ---------------------- パラメータ統合 ---------------------------
    params: Dict[str, Any] = {
        "symbol":     req.symbol or plan.symbol,
        "start":      req.start  or plan.start.isoformat(),
        "end":        req.end    or plan.end.isoformat(),
        "indicators": req.indicators or [],
        "run_no":     req.run_no,
    }

    # symbol が still None → Plan DSL の universe[0] をフォールバック
    if not params["symbol"]:
        universe = getattr(plan, "data", {}).get("universe", [])  # type: ignore[attr-defined]
        if isinstance(universe, list) and universe:
            params["symbol"] = str(universe[0])
        else:
            rec.update(status="FAILED", result={"error": "missing 'symbol'"})
            _save(rec)
            return

    # ------------------------------ 実行 ------------------------------
    try:
        result = run_do(plan.id, params)   # ★ 位置引数 (id, params)

        rec.update(status="DONE", result=result)
        _save(rec)
        logger.info("[Do] ✓ %s DONE", do_id)

    except Exception as exc:               # noqa: BLE001
        rec.update(status="FAILED", result={"error": str(exc)})
        _save(rec)
        logger.error("[Do] ✗ %s FAILED – %s", do_id, exc)
