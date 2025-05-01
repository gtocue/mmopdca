# =========================================================
# ASSIST_KEY: 【api/routers/plan_dsl_api.py】
# =========================================================
#
# Plan-DSL Router
#   • POST /plan-dsl/   : YAML/JSON DSL を登録
#   • GET  /plan-dsl/{id}
#   • GET  /plan-dsl/
# ---------------------------------------------------------
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict

import yaml
from fastapi import APIRouter, HTTPException, Request, UploadFile, File, status

from core.dsl.loader import PlanLoader
from core.repository.factory import get_repo
from core.schemas.plan_schemas import PlanResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/plan-dsl", tags=["plan-dsl"])

_repo:   Any         = get_repo(table="plan")
_loader: PlanLoader  = PlanLoader(validate=True)

# ------------------------------------------------------------------ #
# helpers
# ------------------------------------------------------------------ #
def _ensure_text(data: bytes | str | None) -> str:
    """bytes / str → UTF-8 str。None や空は 400 を投げる"""
    if data is None:
        raise HTTPException(400, detail="Empty body")
    if isinstance(data, bytes):
        if not data.strip():
            raise HTTPException(400, detail="Empty body")
        return data.decode("utf-8")
    if isinstance(data, str):
        txt = data.strip()
        if not txt:
            raise HTTPException(400, detail="Empty body")
        return txt
    raise TypeError("unexpected body type")


def _parse_dsl(text: str) -> Dict[str, Any]:
    """拡張子に頼らず YAML / JSON を自動判定"""
    try:
        return json.loads(text) if text.lstrip().startswith(("{", "[")) else yaml.safe_load(text) or {}
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(400, detail=f"DSL parse error: {exc}") from None


# =====================================================================
# POST /plan-dsl/
# =====================================================================
@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=PlanResponse,
    summary="Create Plan from DSL (YAML / JSON)",
)
async def create_plan_dsl(
    request: Request,
    file: UploadFile | None = File(default=None),           # multipart/form-data
) -> PlanResponse:
    """
    DSL ファイル *または* 生テキスト body を受け取り Plan を登録。

    **PowerShell 例**

    ```powershell
    $yaml = Get-Content .\\samples\\plan_mvp.yaml -Raw
    Invoke-RestMethod `
      -Uri 'http://localhost:8001/plan-dsl/' `
      -Method Post `
      -Body $yaml `
      -ContentType 'application/x-yaml'
    ```
    """
    # ---------- 本文取得 ----------
    if file is not None:                              # multipart
        raw_bytes = await file.read()
        src_name  = file.filename or "upload"
    else:                                             # raw body
        raw_bytes = await request.body()
        src_name  = "inline"

    # ---------- DSL → dict ----------
    plan_dict = _loader.load_dict(_parse_dsl(_ensure_text(raw_bytes)))

    # ---------- plan_id 採番 ----------
    plan_id = plan_dict.get("plan_id") or f"plan_{datetime.utcnow():%y%m%d%H%M%S}"
    if _repo.get(plan_id):
        raise HTTPException(409, detail=f"Plan id '{plan_id}' already exists")

    # ---------- 保存 (legacy dict) ----
    legacy = _loader.legacy_dict(plan_dict)
    legacy.update(id=plan_id, created_at=datetime.now(timezone.utc).isoformat())
    _repo.create(plan_id, legacy)

    logger.info("[Plan-DSL] registered id=%s src=%s", plan_id, src_name)
    return PlanResponse(**legacy)


# =====================================================================
# GET /plan-dsl/{id}
# =====================================================================
@router.get("/{plan_id}", response_model=PlanResponse, summary="Get DSL Plan")
def get_plan_dsl(plan_id: str) -> PlanResponse:
    rec = _repo.get(plan_id)
    if rec is None:
        raise HTTPException(404, detail="Plan not found")
    return PlanResponse(**rec)


# =====================================================================
# GET /plan-dsl/
# =====================================================================
@router.get("/", response_model=list[PlanResponse], summary="List DSL Plans")
def list_plans_dsl() -> list[PlanResponse]:
    return [PlanResponse(**p) for p in _repo.list()]
