# =========================================================
# ASSIST_KEY: このファイルは【api/routers/events_api.py】に位置するユニットです
# =========================================================
#
# 【概要】
#   このユニットは Trace API として、
#   指定された run_id に紐づく進捗イベント（ログ）を SSE/JSONL 形式でストリーミング提供します。
#
# 【主な役割】
#   - Redis や Prefect Checkpoint からログを取得
#   - クライアントへ Server-Sent Events (SSE) でリアルタイム配信
#
# 【連携先・依存関係】
#   - Redis Pub/Sub ブリッジ
#   - Prefect Task Runner のログストア
#   - utils/event_serializer.py
#
# 【ルール遵守】
#   1) SSE ヘッダーは必ず `text/event-stream` とする
#   2) `tail` パラメータで最新n件を遡って送出
#   3) `async def` と `StreamingResponse` を利用
#   4) グローバル変数直書き禁止、依存は依存注入で受け渡す
#   5) 例外時は 404 or 500 を適切に返す
#
# ---------------------------------------------------------

import asyncio
import json
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

from utils.redis_client import get_redis
from utils.event_serializer import serialize_event

router = APIRouter(prefix="/run/{run_id}/events", tags=["events"])


async def event_stream_generator(
    run_id: str, tail: int, redis
) -> AsyncGenerator[str, None]:
    """
    指定 run_id のイベントを Redis Stream から取得し、SSEフォーマットでストリーミング。
    tail: 最新 n 件を最初に送信後、新着を待機して送信する。
    """
    # 最新 tail 件を取得
    try:
        events = redis.xrevrange(f"run_events:{run_id}", count=tail)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Redis error: {e}")

    # 逆順にして古い順で送信
    for entry_id, data in reversed(events):
        payload = serialize_event(entry_id, data)
        yield f"data: {json.dumps(payload)}\n\n"

    last_id = events[0][0] if events else "$"
    # 新着を待機して配信
    while True:
        try:
            results = redis.xread(
                {f"run_events:{run_id}": last_id}, block=60000, count=10
            )
        except Exception:
            await asyncio.sleep(1)
            continue

        for stream, entries in results:
            for entry_id, data in entries:
                payload = serialize_event(entry_id, data)
                yield f"data: {json.dumps(payload)}\n\n"
                last_id = entry_id

        await asyncio.sleep(0.1)


@router.get("/", summary="Trace events for a run", response_class=StreamingResponse)
async def trace_events(
    run_id: str,
    tail: int = Query(
        100, ge=1, le=1000, description="Number of recent events to fetch initially"
    ),
    redis=Depends(get_redis),
):
    """
    GET /run/{run_id}/events?tail=n
    SSE/JSONL 形式で run_id に紐づく進捗ログをストリーミング提供します。
    """
    # TODO: run_id 存在チェック
    generator = event_stream_generator(run_id, tail, redis)
    return StreamingResponse(generator, media_type="text/event-stream")
