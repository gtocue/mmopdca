# api/routers/trace_api.py

from __future__ import annotations

import asyncio
from typing import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from datetime import datetime
from core.repository.factory import get_repo

router = APIRouter(
    prefix="/trace",
    tags=["trace"],
    responses={404: {"description": "Not Found"}},
)

# --------------------------------------------------------------------- #
# Pydantic model for incoming trace POST (if needed later)
# --------------------------------------------------------------------- #
class TraceRecord(BaseModel):
    run_id: str = Field(..., description="一意のジョブ実行ID")
    step: str = Field(..., description="処理ステップ名")
    status: str = Field(..., description="STARTED／COMPLETED／FAILED")
    timestamp: datetime = Field(..., description="ISO8601形式タイムスタンプ")
    details: dict[str, any] = Field(default_factory=dict, description="任意の追加情報")

# --------------------------------------------------------------------- #
# Internal: 擬似 SSE ストリーム
# --------------------------------------------------------------------- #
async def _event_stream(run_id: str) -> AsyncIterator[str]:
    """
    run_id に対して0.5秒おきに5件の JSON 行を送信する簡易 SSE。
    本番では Redis Streams や DB から実データを取得して流す想定。
    """
    repo = get_repo("trace")  # repository instance (in-memory or persistent)
    for step in range(1, 6):
        # In a real implementation, you would fetch the next TraceRecord from repo:
        # record = repo.get_next(run_id)
        # yield f"data: {record.json()}\n\n"
        # For MVP, fabricate a record:
        record = {
            "run_id": run_id,
            "step": step,
            "status": "COMPLETED" if step > 1 else "STARTED",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "details": {"records_processed": step * 10}
        }
        await asyncio.sleep(0.5)
        yield f"data: {record!r}\n\n"

# --------------------------------------------------------------------- #
# Trace stream (SSE) endpoint
# --------------------------------------------------------------------- #
@router.get(
    "/{run_id}",
    response_class=StreamingResponse,
    summary="Trace stream (SSE)",
    description="Server-Sent Events でジョブの進捗を配信します。"
)
async def trace_events(run_id: str) -> StreamingResponse:
    """
    text/event-stream を返し、ブラウザの EventSource で受信可能な SSE エンドポイント。
    """
    # Optionally verify run_id exists:
    repo = get_repo("trace")
    if not repo.exists(run_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="run_id not found")

    return StreamingResponse(_event_stream(run_id), media_type="text/event-stream")
