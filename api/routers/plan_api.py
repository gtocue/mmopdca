# =========================================================
# ASSIST_KEY: 【api/routers/plan_api.py】
# =========================================================
#
# 【概要】
#   PlanRouter ― “Plan（命令書）” を CRUD する REST エンドポイント。
#
# 【主な役割】
#   - POST  /plan/        : Plan の新規登録
#   - GET   /plan/{id}    : 1 件取得
#   - GET   /plan/        : 一覧取得
#   - DELETE/plan/{id}    : 削除
#
# 【連携先・依存関係】
#   - core.schemas.plan_schemas.PlanCreateRequest / PlanResponse
#   - core.repository.factory.get_repo
#
# 【ルール遵守】
#   1) メイン銘柄 "Close_main" / "Open_main" は直接扱わない
#   2) 市場は suffix 付き列名で区別（例: "Close_SP500"）
#   3) **全体コード** を返す
#   4) 本ヘッダーは必ず残す
#   5) 機能削除は事前相談（今回は追加のみ）
#   6) pdca_data[...] に統一（※本ユニットは pdca_data を直接扱わない）
# ---------------------------------------------------------

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Response, status

from core.schemas.plan_schemas import PlanCreateRequest, PlanResponse
from core.repository.factory import get_repo

router = APIRouter(prefix="/plan", tags=["plan"])

# --------------------------------------------------
# Repository の DI
# --------------------------------------------------
_repo = get_repo(table="plan")


# ==================================================
# POST /plan/  ― Create
# ==================================================
@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=PlanResponse,
    summary="Create Plan",
)
def create_plan(req: PlanCreateRequest) -> PlanResponse:
    """
    新しい Plan を登録する。

    * `id` を省略すると `plan_<8桁>` を自動採番。
    * 同じ `id` が既にあれば **409 Conflict**。
    """
    plan_id: str = req.id or f"plan_{uuid4().hex[:8]}"

    if _repo.get(plan_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Plan id '{plan_id}' already exists",
        )

    doc = req.model_copy(update={"id": plan_id}).model_dump(mode="json")
    doc["created_at"] = datetime.now(timezone.utc).isoformat()

    _repo.create(plan_id, doc)
    return PlanResponse(**doc)


# ==================================================
# GET /plan/{id}  ― Read-One
# ==================================================
@router.get(
    "/{plan_id}",
    response_model=PlanResponse,
    summary="Get Plan by ID",
)
def get_plan(plan_id: str) -> PlanResponse:
    plan = _repo.get(plan_id)
    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan '{plan_id}' not found",
        )
    return PlanResponse(**plan)


# ==================================================
# GET /plan/  ― Read-All
# ==================================================
@router.get(
    "/",
    response_model=list[PlanResponse],
    summary="List Plans",
)
def list_plans() -> list[PlanResponse]:
    return [PlanResponse(**p) for p in _repo.list()]


# ==================================================
# DELETE /plan/{id}  ― Delete
# ==================================================
@router.delete(
    "/{plan_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Plan",
)
def delete_plan(plan_id: str) -> Response:
    if _repo.get(plan_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan '{plan_id}' not found",
        )

    _repo.delete(plan_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
