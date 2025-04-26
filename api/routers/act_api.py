from __future__ import annotations

import uuid
from datetime import datetime
from typing import Dict

from fastapi import APIRouter, HTTPException, Path
from pydantic import BaseModel, Field

# ──────────────────────────────────────────────
# Models
# ──────────────────────────────────────────────
class ActDecision(BaseModel):
    id: str = Field(default_factory=lambda: f"act-{uuid.uuid4().hex[:8]}")
    check_id: str
    decided_at: datetime = Field(default_factory=datetime.utcnow)
    action: str = "noop"             # e.g. "retrain", "alert", "noop"
    reason: str = "stub — always noop"

# ──────────────────────────────────────────────
# Store
# ──────────────────────────────────────────────
_store: Dict[str, ActDecision] = {}

# ──────────────────────────────────────────────
# Router
# ──────────────────────────────────────────────
router = APIRouter(prefix="/act", tags=["act"])


@router.post("/{check_id}", response_model=ActDecision, status_code=201)
async def run_act(check_id: str = Path(..., description="Check ID to act on")) -> ActDecision:
    """
    Check の結果を受けて自動アクションを決定する（ダミー: 常に noop）
    """
    ac = ActDecision(check_id=check_id)
    _store[ac.id] = ac
    return ac


@router.get("/{act_id}", response_model=ActDecision)
async def get_act(act_id: str) -> ActDecision:
    if act_id not in _store:
        raise HTTPException(404, detail="ActDecision not found")
    return _store[act_id]


@router.get("/", response_model=list[ActDecision])
async def list_act() -> list[ActDecision]:
    return list(_store.values())
