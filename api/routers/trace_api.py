# ─── api/routers/trace_api.py ───────────────────────────────────────────
"""
Trace API  (Server-Sent Events)

GET /trace/{run_id}  → text/event-stream
疑似データを 5 件送る MVP 実装。後で Redis Streams / DB 連携に差し替え予定。
"""
from __future__ import annotations

import asyncio
from typing import AsyncIterator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/trace", tags=["trace"])


# --------------------------------------------------------------------- #
# 内部: 擬似 SSE ストリーム
# --------------------------------------------------------------------- #
async def _event_stream(run_id: str) -> AsyncIterator[str]:
    """
    run_id に対して 0.5 秒おきに 5 件の JSON 行を送信する簡易 SSE。
    本番では DB / Redis Streams から実データを取得して流す想定。
    """
    for step in range(1, 6):
        await asyncio.sleep(0.5)
        yield f'data: {{"run_id": "{run_id}", "step": {step}}}\n\n'


# --------------------------------------------------------------------- #
# エンドポイント
# --------------------------------------------------------------------- #
@router.get("/{run_id}", response_class=StreamingResponse, summary="Trace stream (SSE)")
async def trace_events(run_id: str) -> StreamingResponse:  # noqa: D401 – FastAPI handler
    """
    Server-Sent Events でジョブの進捗を配信するエンドポイント (MVP)。
    `text/event-stream` を返し、ブラウザ `EventSource` で受信可能。
    """
    return StreamingResponse(_event_stream(run_id), media_type="text/event-stream")
