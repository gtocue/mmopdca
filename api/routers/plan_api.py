# =========================================================
# ASSIST_KEY: このファイルは【api/routers/plan_api.py】に位置するユニットです
# =========================================================
#
# 【概要】
#   PlanRouter ― “Plan（命令書）” を CRUD する REST エンドポイント。
#
# 【主な役割】
#   - POST /plan/        : Plan の新規登録
#   - GET  /plan/{id}    : 1 件取得
#   - GET  /plan/        : 一覧取得
#   - DELETE /plan/{id}  : 削除
#
# 【連携先・依存関係】
#   - core.schemas.command.PlanCommand  … 型バリデーション
#   - core.repository.factory.get_repo  … Memory / SQLite 切替
#
# 【ルール遵守】
#   1) メイン銘柄 "Close_main" / "Open_main" は直接扱わない
#   2) 市場は suffix 付き列名で区別（例: "Close_SP500"）
#   3) **全体コード** を返す
#   4) 本ヘッダーは必ず残す
#   5) 機能削除は事前相談（今回は追加のみ）
#   6) pdca_data[...] に統一（※本ユニットは pdca_data を直接扱わない）
#
# ---------------------------------------------------------

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from core.schemas.command import PlanCommand
from core.repository.factory import get_repo

router = APIRouter(prefix="/plan", tags=["plan"])

# --------------------------------------------------
# Repository を DI で取得
#   - DB_BACKEND=memory  … インメモリ
#   - DB_BACKEND=sqlite  … SQLite 永続化（mmopdca.db）
# --------------------------------------------------
_repo = get_repo(table="plan")

# ==================================================
# POST /plan/  ― Create
# ==================================================
@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    summary="Create Plan",
)
def create_plan(cmd: PlanCommand):
    """
    Plan を登録。`id` が重複している場合は **409 Conflict** を返す。
    """
    if _repo.get(cmd.id):
        raise HTTPException(409, "id already exists")

    _repo.create(cmd.id, cmd.model_dump(mode="json"))
    return {"ok": True, "id": cmd.id}


# ==================================================
# GET /plan/{id}  ― Read-One
# ==================================================
@router.get(
    "/{cmd_id}",
    response_model=PlanCommand,
    summary="Get Plan",
)
def get_plan(cmd_id: str):
    plan = _repo.get(cmd_id)
    if plan is None:
        raise HTTPException(404, "not found")
    return PlanCommand(**plan)  # 型を復元して返却


# ==================================================
# GET /plan/  ― Read-All
# ==================================================
@router.get(
    "/",
    response_model=list[PlanCommand],
    summary="List Plans",
)
def list_plans() -> list[PlanCommand]:
    return [PlanCommand(**p) for p in _repo.list()]


# ==================================================
# DELETE /plan/{id}  ― Delete
# ==================================================
@router.delete(
    "/{cmd_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Plan",
)
def delete_plan(cmd_id: str):
    """
    Plan を削除。存在しなければ **404 Not Found**。
    """
    if _repo.get(cmd_id) is None:
        raise HTTPException(404, "not found")
    _repo.delete(cmd_id)     # MemoryRepository / SQLiteRepository ともに delete 実装済み
