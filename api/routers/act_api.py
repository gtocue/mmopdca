# =========================================================
# ASSIST_KEY: このファイルは【api/routers/act_api.py】に位置するユニットです
# =========================================================
#
# 【概要】
#   ActRouter ― CheckResult を評価し ActDecision を生成する
#
# 【主な役割】
#   - POST /act/{check_id} : Check を読み取り decision_engine で判定
#   - GET  /act/{act_id}   : 1 件取得
#   - GET  /act/           : 一覧
#
# 【連携先・依存関係】
#   - core/act/decision_engine.py → decide(check) を呼び出す
#   - Repository : check / act テーブル
#
# 【ルール遵守】
#   1) メイン銘柄 "Close_main" / "Open_main" は直接扱わない
#   2) 市場は suffix 列名で区別
#   3) 本ヘッダーを残す
# ---------------------------------------------------------

from __future__ import annotations

from typing import List

from fastapi import APIRouter, HTTPException, Path, status

from core.repository.factory import get_repo
from core.schemas.act_schemas import ActDecision
from core.schemas.check_schemas import CheckResult
from core.act.decision_engine import decide

router = APIRouter(prefix="/act", tags=["act"])

# ──────────────────────────────────────────────
# Repository インスタンス（メモリ or SQLite）
# ──────────────────────────────────────────────
_act_repo = get_repo(table="act")
_check_repo = get_repo(table="check")


# =========================================================
# POST /act/{check_id}  ― ActDecision 作成
# =========================================================
@router.post(
    "/{check_id}",
    response_model=ActDecision,
    status_code=status.HTTP_201_CREATED,
    summary="Run Act (decide next action)",
)
def create_act(
    check_id: str = Path(..., description="Check ID to act on"),
) -> ActDecision:
    # 1) Check をロード
    raw = _check_repo.get(check_id)
    if raw is None:
        raise HTTPException(404, detail="CheckResult not found")
    check = CheckResult.model_validate(raw)

    # 2) 意思決定
    decision = decide(check)

    # 3) 保存
    _act_repo.create(decision.id, decision.model_dump(mode="json"))
    return decision


# =========================================================
# GET /act/{act_id}  ― 1 件取得
# =========================================================
@router.get(
    "/{act_id}",
    response_model=ActDecision,
    summary="Get ActDecision",
)
def get_act(act_id: str) -> ActDecision:
    raw = _act_repo.get(act_id)
    if raw is None:
        raise HTTPException(404, detail="ActDecision not found")
    return ActDecision.model_validate(raw)


# =========================================================
# GET /act/  ― 一覧
# =========================================================
@router.get(
    "/",
    response_model=List[ActDecision],
    summary="List ActDecision",
)
def list_act() -> List[ActDecision]:
    return [ActDecision.model_validate(r) for r in _act_repo.list()]
