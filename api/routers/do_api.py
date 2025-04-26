# =========================================================
# ASSIST_KEY: このファイルは【api/routers/do_api.py】に位置するユニットです
# =========================================================
#
# 【概要】
#   DoRouter ― Plan で定義されたジョブを「Do フェーズ」として実行する
#   HTTP API を提供する。
#
# ---------------------------------------------------------

from __future__ import annotations

import uuid
from typing import List

from fastapi import APIRouter, BackgroundTasks, HTTPException, status

from core.do.coredo_executor import run_do
from core.schemas.do_schemas import DoCreateRequest, DoResponse
from core.repository.factory import get_repo

router = APIRouter(prefix="/do", tags=["do"])

# ──────────────────────────────────────────────────────────
# バックエンドは環境変数 DB_BACKEND=memory|sqlite|postgres で自動判定
# ──────────────────────────────────────────────────────────
_do_repo = get_repo("do")          # public.do などに自動生成


# =========================================================
# POST /do/{plan_id}  ― Do 実行
# =========================================================
@router.post(
    "/{plan_id}",
    response_model=DoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Run Do",
)
async def create_do(
    plan_id: str,
    body: DoCreateRequest,
    bg: BackgroundTasks,
) -> DoResponse:
    """
    指定された Plan を Do フェーズで実行する。
    """
    do_id = f"do-{uuid.uuid4().hex[:8]}"

    record = {
        "do_id":    do_id,
        "plan_id":  plan_id,
        "status":   "PENDING",
        "result":   None,
    }
    _do_repo.create(do_id, record)          # ★ ここが辞書→Repo へ

    # バックグラウンド実行
    bg.add_task(_execute_do_async, do_id, plan_id, body)

    return DoResponse(**record)


# =========================================================
# GET /do/{do_id}
# =========================================================
@router.get("/{do_id}", response_model=DoResponse, summary="Get Do")
async def get_do(do_id: str) -> DoResponse:
    rec = _do_repo.get(do_id)
    if rec is None:
        raise HTTPException(404, "Do not found")
    return DoResponse(**rec)


# =========================================================
# GET /do/
# =========================================================
@router.get("/", response_model=list[DoResponse], summary="List Do")
async def list_do() -> list[DoResponse]:
    return [DoResponse(**r) for r in _do_repo.list()]


# ---------------------------------------------------------
# internal helpers
# ---------------------------------------------------------
def _execute_do_async(
    do_id: str,
    plan_id: str,
    params: DoCreateRequest,
) -> None:
    """同期で run_do を呼び出し、Repo に状態を反映する"""
    def _save(state: dict) -> None:
        """後方互換の無い簡易 upsert（delete→create）"""
        _do_repo.delete(do_id)
        _do_repo.create(do_id, state)

    # RUNNING
    rec = _do_repo.get(do_id)
    rec["status"] = "RUNNING"
    _save(rec)

    # 実ジョブ
    try:
        result = run_do(plan_id, params.model_dump())

        rec["status"] = "DONE"
        rec["result"] = result
        _save(rec)

    except Exception as exc:        # noqa: BLE001
        rec["status"] = "FAILED"
        rec["result"] = {"error": str(exc)}
        _save(rec)
