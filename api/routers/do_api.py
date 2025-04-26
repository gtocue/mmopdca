# =========================================================
# ASSIST_KEY: このファイルは【api/routers/do_api.py】に位置するユニットです
# =========================================================
#
# 【概要】
#   このユニットは DoRouter として、
#   既存 Plan の実行（特徴量生成＋モデル推論）を HTTP API で公開します。
#
# 【主な役割】
#   - POST /do/{plan_id}  : Plan を受け取り Do を非同期実行
#   - GET  /do/{do_id}    : 単一 Do 結果を取得
#   - GET  /do/           : Do 一覧を返す
#
# 【連携先・依存関係】
#   - 他ユニット :
#       ・core/do/coredo_executor.py          … Do 処理の本体
#       ・core/plan/plan_repository.py (予定)… Plan の取得
#   - 外部設定 :
#       ・pdca_data["do"] 共有ストア
#       ・settings/do.yaml（TODO: ジョブキュー設定）
#
# 【ルール遵守】
#   1) メイン銘柄 "Close_main" / "Open_main" は直接扱わない
#   2) 市場名 suffix で区別（例: "Close_SP500"）
#   3) **全体コード** を返却
#   4) 本ヘッダーは必ず残す
#   5) 機能削除は要相談
#   6) pdca_data[...] に統一
#
# 【注意事項】
#   - 現段階ではインメモリ辞書で擬似永続化。後に DB / メッセージブローカへ置換予定
#   - バックグラウンド処理は Celery/Kafka 連携を見越し async stub 実装
# ---------------------------------------------------------

from __future__ import annotations

import uuid
from typing import Dict, List

from fastapi import APIRouter, BackgroundTasks, HTTPException, status

from core.do.coredo_executor import run_do  # Do 本体
from core.schemas.do_schemas import DoCreateRequest, DoResponse   # ←schemas 追加予定

router = APIRouter(prefix="/do", tags=["do"])

# ―――――――――――――――――――――――――――――――――――――――
# 仮ストア（TODO: DB / Redis へ移行）
# ―――――――――――――――――――――――――――――――――――――――
_PDCA_DO_STORE: Dict[str, Dict] = {}


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
):
    """
    指定された Plan を Do フェーズで実行し
    特徴量計算 → モデル推論 → 結果を pdca_data["do"] に保存します。
    """
    do_id = f"do-{uuid.uuid4().hex[:8]}"
    _PDCA_DO_STORE[do_id] = {
        "plan_id": plan_id,
        "status": "PENDING",
        "result": None,
    }

    # バックグラウンドで実処理
    bg.add_task(_execute_do_async, do_id, plan_id, body)

    return {"do_id": do_id, "status": "PENDING"}


# =========================================================
# GET /do/{do_id}  ― Do 結果取得
# =========================================================
@router.get(
    "/{do_id}",
    response_model=DoResponse,
    summary="Get Do",
)
async def get_do(do_id: str):
    if do_id not in _PDCA_DO_STORE:
        raise HTTPException(status_code=404, detail="Do not found")
    return _PDCA_DO_STORE[do_id]


# =========================================================
# GET /do/  ― Do 一覧
# =========================================================
@router.get(
    "/",
    response_model=List[DoResponse],
    summary="List Do",
)
async def list_do():
    return list(_PDCA_DO_STORE.values())


# ---------------------------------------------------------
# internal helpers
# ---------------------------------------------------------
def _execute_do_async(do_id: str, plan_id: str, params: DoCreateRequest) -> None:
    """同期関数として実 Do 処理を呼び出し、ストアを更新"""
    try:
        _PDCA_DO_STORE[do_id]["status"] = "RUNNING"
        result = run_do(plan_id, params.dict())  # 実処理
        _PDCA_DO_STORE[do_id]["status"] = "DONE"
        _PDCA_DO_STORE[do_id]["result"] = result
    except Exception as ex:  # noqa: BLE001
        _PDCA_DO_STORE[do_id]["status"] = "ERROR"
        _PDCA_DO_STORE[do_id]["result"] = str(ex)
