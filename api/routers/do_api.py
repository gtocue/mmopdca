# =====================================================================
# api/routers/do_api.py
# ---------------------------------------------------------------------
#   “Do フェーズ” Router  –  Celery を使わず **同期** で run_do() を実行
#
#     • POST /do/{plan_id}   : ジョブ登録（即 201）
#     • GET  /do/{do_id}     : 単一取得
#     • GET  /do/            : 一覧取得
#
#   - Plan が無ければ 404
#   - Repository は core.repository.factory.get_repo() で動的に切替
# =====================================================================
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, status

from core.do.coredo_executor import run_do                     # ★ 直接実行
from core.repository.factory import get_repo
from core.schemas.do_schemas import DoCreateRequest, DoResponse
from core.schemas.plan_schemas import PlanResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/do", tags=["do"])

# ------------------------------------------------------------------ #
# Repository  – env(DB_BACKEND) に応じて memory / sqlite / postgres …
# ------------------------------------------------------------------ #
_do_repo   = get_repo(table="do")
_plan_repo = get_repo(table="plan")

# ================================================================== #
# POST /do/{plan_id}  ―― 同期 run_do() をバックグラウンド起動
# ================================================================== #
@router.post(
    "/{plan_id}",
    response_model=DoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Enqueue Do job (thread-pool sync)",
)
def enqueue_do(
    plan_id: str,
    bg: BackgroundTasks,
    body: Optional[DoCreateRequest] = None,
) -> DoResponse:
    """
    指定 Plan を **バックグラウンドスレッド** で run_do() しながら  
    直ちに DoRecord (status=PENDING) を返す。
    """
    # --- Plan 存在確認 ------------------------------------------------
    plan_raw: Dict[str, Any] | None = _plan_repo.get(plan_id)
    if plan_raw is None:
        raise HTTPException(404, detail=f"Plan '{plan_id}' not found")

    plan = PlanResponse(**plan_raw)
    req  = body or DoCreateRequest()

    # --- run_no / seq 補完 -------------------------------------------
    run_no = req.run_no or req.seq or 1
    req.run_no = run_no
    req.seq    = run_no          # レスポンス互換

    # --- Do レコード初期化 -------------------------------------------
    do_id = f"do-{uuid.uuid4().hex[:8]}"
    record = {
        "do_id":         do_id,
        "plan_id":       plan_id,
        "seq":           run_no,
        "run_tag":       req.run_tag,
        "status":        "PENDING",
        "result":        None,
        "dashboard_url": None,
        "created_at":    datetime.now(timezone.utc).isoformat(),
    }
    _do_repo.create(do_id, record)

    # --- バックグラウンド実行 ----------------------------------------
    bg.add_task(_execute_do_sync, do_id, plan, req)

    return DoResponse(**record)


# ================================================================== #
# GET /do/{do_id}
# ================================================================== #
@router.get("/{do_id}", response_model=DoResponse, summary="Get Do job")
def get_do(do_id: str) -> DoResponse:
    rec = _do_repo.get(do_id)
    if rec is None:
        raise HTTPException(404, detail="Do job not found")
    return DoResponse(**rec)


# ================================================================== #
# GET /do/
# ================================================================== #
@router.get("/", response_model=List[DoResponse], summary="List Do jobs")
def list_do() -> List[DoResponse]:
    return [DoResponse(**r) for r in _do_repo.list()]


# ------------------------------------------------------------------ #
# internal helpers
# ------------------------------------------------------------------ #
def _execute_do_sync(
    do_id: str,
    plan: PlanResponse,
    req: DoCreateRequest,
) -> None:
    """スレッドプールで呼ばれ、run_do() を同期実行して結果を保存。"""

    def _save(state: Dict[str, Any]) -> None:
        # MemoryRepository 等では upsert が無いので簡易 upsert
        _do_repo.delete(do_id)
        _do_repo.create(do_id, state)

    # ------------------- RUNNING フラグに更新 -------------------------
    rec = _do_repo.get(do_id) or {}
    rec["status"] = "RUNNING"
    _save(rec)

    # ------------------- 実行パラメータ統合 ---------------------------
    params: Dict[str, Any] = {
        "symbol":     req.symbol or plan.symbol,
        "start":      req.start  or plan.start.isoformat(),
        "end":        req.end    or plan.end.isoformat(),
        "indicators": req.indicators or [],
        "run_no":     req.run_no,
    }
    # Plan DSL (data.universe) フォールバック
    if not params["symbol"]:
        universe = getattr(plan, "data", {}).get("universe", [])  # type: ignore[attr-defined]
        if isinstance(universe, list) and universe:
            params["symbol"] = str(universe[0])
        else:
            rec.update(status="FAILED", result={"error": "missing 'symbol'"})
            _save(rec)
            return

    # ------------------- 実際の Do 処理 ------------------------------
    try:
        result = run_do(plan.id, params)

        rec.update(status="DONE", result=result)
        _save(rec)
        logger.info("[Do] ✓ %s DONE", do_id)

    except Exception as exc:                                   # noqa: BLE001
        rec.update(status="FAILED", result={"error": str(exc)})
        _save(rec)
        logger.exception("[Do] ✗ %s FAILED – %s", do_id, exc)
