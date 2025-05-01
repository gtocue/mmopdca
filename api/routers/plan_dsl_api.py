# =========================================================
# ASSIST_KEY: 【api/routers/plan_dsl_api.py】
# =========================================================
#
# 【概要】
#   このユニットは PlanDslRouter として、
#   “DSL（YAML / JSON）形式の Plan” を登録・取得します。
#
# 【主な役割】
#   - POST /plan-dsl/          : DSL を受け取り Plan 登録
#   - GET  /plan-dsl/{id}      : 単一 Plan 取得
#   - GET  /plan-dsl/          : 一覧取得
#
# 【連携先・依存関係】
#   - core.dsl.loader.PlanLoader        : defaults マージ & schema 検証
#   - core.repository.factory.get_repo  : Plan 保存／取得
#
# 【ルール遵守】
#   1) 既存 plan_api を壊さない（別 prefix）
#   2) 型安全・ハルシネーション禁止
#   3) **全体コード** を返却
#   4) 機能削除や breaking change は事前相談（追加のみ）
#   5) pdca_data[...] 直書き禁止（本ユニットはリポジトリ経由）
# ---------------------------------------------------------

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated, Any, Dict

import yaml
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from core.dsl.loader import PlanLoader
from core.repository.factory import get_repo
from core.schemas.plan_schemas import PlanResponse  # 既存スキーマを再利用

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/plan-dsl", tags=["plan-dsl"])

_repo = get_repo(table="plan")
_loader = PlanLoader(validate=True)  # jsonschema 未インストール時は内部で自動スキップ

# ---------------------------------------------------------------------
# internal helpers
# ---------------------------------------------------------------------
def _bytes_to_str(raw: bytes | None) -> str:
    """UploadFile / body bytes いずれも UTF-8 文字列へ統一"""
    if raw is None or not raw.strip():
        raise HTTPException(status_code=400, detail="Empty body")
    return raw.decode("utf-8")


def _parse_dsl(text: str) -> Dict[str, Any]:
    """
    YAML / JSON を自動判定して dict へ。
    * core.dsl.loader に load_text() が無い場合のフォールバック
    """
    text_s = text.lstrip()
    try:
        if text_s.startswith(("{", "[")):
            return json.loads(text)
        return yaml.safe_load(text) or {}
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"DSL parse error: {exc}") from None


# ---------------------------------------------------------------------
# POST /plan-dsl/  ― Create
# ---------------------------------------------------------------------
@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=PlanResponse,
    summary="Create Plan from DSL (YAML / JSON)",
)
async def create_plan_dsl(
    file: UploadFile | None = File(default=None),
    body: Annotated[bytes | None, File(media_type="application/octet-stream")] = None,
) -> PlanResponse:
    """
    DSL ファイル（multipart/form-data）または生テキスト body から Plan を登録。  
    - Content-Type: `application/x-yaml` / `application/json` / `multipart/form-data`
    - `plan_id` が無い場合は `plan_<8桁>` を自動採番
    """
    raw_bytes: bytes | None
    src_name: str

    if file is not None:  # multipart
        raw_bytes = await file.read()
        src_name = file.filename or "upload"
    else:                 # 直接 body
        raw_bytes = body
        src_name = "inline"

    text = _bytes_to_str(raw_bytes)
    plan_dict = _parse_dsl(text)               # dict へパース
    plan_dict = _loader.load_dict(plan_dict)   # defaults マージ + schema 検証

    plan_id: str = plan_dict.get("plan_id") or f"plan_{datetime.now().strftime('%y%m%d%H%M')}"
    if _repo.get(plan_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Plan id '{plan_id}' already exists",
        )

    # ----- legacy dict へ射影して保存 -------------------------
    legacy = _loader.legacy_dict(plan_dict)
    legacy["id"] = plan_id            # 既存 PlanResponse 互換
    legacy["created_at"] = datetime.now(timezone.utc).isoformat()
    _repo.create(plan_id, legacy)

    logger.info("[Plan-DSL] ✓ %s registered (src=%s)", plan_id, src_name)
    return PlanResponse(**legacy)


# ---------------------------------------------------------------------
# GET /plan-dsl/{id}
# ---------------------------------------------------------------------
@router.get(
    "/{plan_id}",
    response_model=PlanResponse,
    summary="Get DSL Plan",
)
def get_plan_dsl(plan_id: str) -> PlanResponse:
    plan = _repo.get(plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="Plan not found")
    return PlanResponse(**plan)


# ---------------------------------------------------------------------
# GET /plan-dsl/
# ---------------------------------------------------------------------
@router.get(
    "/",
    response_model=list[PlanResponse],
    summary="List DSL Plans",
)
def list_plans_dsl() -> list[PlanResponse]:
    return [PlanResponse(**p) for p in _repo.list()]
