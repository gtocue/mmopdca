from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from core.repository.factory import get_repo

router = APIRouter(prefix="/ai-key", tags=["ai-key"])

_repo = get_repo("ai_key")


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    summary="Create AI key",
)
def create_ai_key() -> JSONResponse:
    key = uuid.uuid4().hex
    now = datetime.now(timezone.utc).isoformat()
    _repo.create(key, {"id": key, "created_at": now})
    return JSONResponse(status_code=status.HTTP_201_CREATED, content={"key": key})


@router.get(
    "/{key}",
    summary="Get AI key",
)
def get_ai_key(key: str) -> Dict[str, Any]:
    rec = _repo.get(key)
    if rec is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="AI key not found")
    return rec


@router.get(
    "/",
    summary="List AI keys",
)
def list_ai_keys() -> List[Dict[str, Any]]:
    return list(_repo.list())