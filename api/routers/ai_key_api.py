"""AI-Key PoC router (Sprint-2 #2-3).

- POST /ai-key/         … 新しい API キーを発行して返す
- GET  /ai-key/{key_id} … 登録済みキーのメタ情報を返す
※ストレージはメモリ辞書。プロセス再起動で消える PoC 版。
"""
from __future__ import annotations

import secrets
import uuid
from datetime import datetime, timezone
from typing import Final

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

router: Final = APIRouter(prefix="/ai-key", tags=["ai-key"])

# ───────────── In-memory store ──────────────
_STORE: dict[str, "AIKey"] = {}


class AIKey(BaseModel):
    id: str = Field(description="UUID4 文字列")
    key: str = Field(description="実際に HTTP Header に乗る値")
    created_at: datetime


# ───────────── Endpoints ─────────────────────
@router.post("/", response_model=AIKey, status_code=status.HTTP_201_CREATED)
def create_key() -> AIKey:
    key_obj = AIKey(
        id=str(uuid.uuid4()),
        key=secrets.token_urlsafe(32),
        created_at=datetime.now(timezone.utc),
    )
    _STORE[key_obj.id] = key_obj
    return key_obj


@router.get("/{key_id}", response_model=AIKey)
def get_key(key_id: str) -> AIKey:
    if key_id not in _STORE:
        raise HTTPException(status_code=404, detail="AI-Key not found")
    return _STORE[key_id]
