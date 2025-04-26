from __future__ import annotations

import uuid
from datetime import datetime
from typing import Dict

from fastapi import APIRouter, HTTPException, Path
from pydantic import BaseModel, Field

# ──────────────────────────────────────────────
# Models
# ──────────────────────────────────────────────
class CheckResult(BaseModel):
    id: str = Field(default_factory=lambda: f"check-{uuid.uuid4().hex[:8]}")
    do_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    report: dict = {"accuracy": 0.9}  # ←ダミー

# ──────────────────────────────────────────────
# Store
# ──────────────────────────────────────────────
_store: Dict[str, CheckResult] = {}

# ──────────────────────────────────────────────
# Router
# ──────────────────────────────────────────────
router = APIRouter(prefix="/check", tags=["check"])


@router.post("/{do_id}", response_model=CheckResult, status_code=201)
async def run_check(do_id: str = Path(..., description="Do ID to evaluate")) -> CheckResult:
    """DoResult を評価してメトリクスをまとめる（ダミー実装）"""
    ck = CheckResult(do_id=do_id)
    _store[ck.id] = ck
    return ck


@router.get("/{check_id}", response_model=CheckResult)
async def get_check(check_id: str) -> CheckResult:
    if check_id not in _store:
        raise HTTPException(404, detail="CheckResult not found")
    return _store[check_id]


@router.get("/", response_model=list[CheckResult])
async def list_check() -> list[CheckResult]:
    return list(_store.values())
