# =========================================================
# api/routers/do_api.py
# ---------------------------------------------------------
#  ● DoRouter ― Plan で定義されたシナリオを “Do フェーズ” として実行する
#    HTTP API（非同期 BG 実行 + CRUD）を提供する。
#
#      POST   /do/{plan_id}   : Do ジョブ生成 (BG 実行開始)   201
#      GET    /do/{do_id}     : 単一 Do の状態 / 結果取得       200
#      GET    /do/            : Do 一覧取得                     200
#
#  ☆ 同一 Plan に対し何度でも Do を走らせられる（do-UUID 管理）
#  ☆ 各レコードは repo(key=do_id) に {plan_id, status, result, …}
#    として保存。バックエンドは env[DB_BACKEND] = memory|sqlite|postgres
#    で自動切り替え（core.repository.factory.get_repo を使用）
# =========================================================

from __future__ import annotations

import uuid
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, status

from core.do.coredo_executor import run_do
from core.schemas.do_schemas import DoCreateRequest, DoResponse
from core.repository.factory import get_repo

router = APIRouter(prefix="/do", tags=["do"])

# ------------------------------------------------------------------
# Repository を DI。table="do" は自動で作成される
#   memory   : インメモリ辞書
#   sqlite   : ./mmopdca.db の do テーブル
#   postgres : public.do テーブル
# ------------------------------------------------------------------
_do_repo = get_repo(table="do")

# =========================================================
# POST /do/{plan_id}  ― Do 実行エンドポイント
# =========================================================
@router.post(
    "/{plan_id}",
    response_model=DoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Run Do",
)
async def create_do(                       # noqa: D401
    plan_id: str,
    bg: BackgroundTasks,
    body: Optional[DoCreateRequest] = None,
) -> DoResponse:
    """
    指定した *Plan* を **Do フェーズ** でバックグラウンド実行します。

    - 受け付け後すぐ `201 Created` を返し、実処理は非同期で開始  
    - 1 Plan ≫ n Do を許容（毎回新しい `do-xxxxxxxx` を採番）  
    - 進捗は `status=PENDING|RUNNING|DONE|FAILED` で追跡  
    """
    do_id = f"do-{uuid.uuid4().hex[:8]}"
    record = {
        "do_id":   do_id,
        "plan_id": plan_id,
        "status":  "PENDING",
        "result":  None,
    }
    _do_repo.create(do_id, record)

    # BG スレッドで同期関数を呼び出す
    bg.add_task(_execute_do_sync, do_id, plan_id, body or DoCreateRequest())

    return DoResponse(**record)


# =========================================================
# GET /do/{do_id}  ― 単一取得
# =========================================================
@router.get("/{do_id}", response_model=DoResponse, summary="Get Do")
async def get_do(do_id: str) -> DoResponse:
    rec = _do_repo.get(do_id)
    if rec is None:
        raise HTTPException(404, "Do not found")
    return DoResponse(**rec)


# =========================================================
# GET /do/  ― 一覧取得
# =========================================================
@router.get("/", response_model=List[DoResponse], summary="List Do")
async def list_do() -> List[DoResponse]:
    return [DoResponse(**r) for r in _do_repo.list()]


# ------------------------------------------------------------------
# internal helpers
# ------------------------------------------------------------------
def _execute_do_sync(
    do_id: str,
    plan_id: str,
    params: DoCreateRequest,
) -> None:
    """
    `run_do()` を同期実行し、Repo に
        RUNNING → DONE / FAILED
    をアトミックに反映するヘルパ。
    """

    def _save(state: dict) -> None:
        """簡易 Upsert（delete → create）。SQLite/Postgres 両対応"""
        _do_repo.delete(do_id)
        _do_repo.create(do_id, state)

    # --- RUNNING ---
    rec = _do_repo.get(do_id) or {}
    rec.update(status="RUNNING")
    _save(rec)

    # --- 実ジョブ ---
    try:
        result = run_do(plan_id, params.model_dump())

        rec.update(status="DONE", result=result)
        _save(rec)

    except Exception as exc:  # noqa: BLE001
        rec.update(status="FAILED", result={"error": str(exc)})
        _save(rec)
