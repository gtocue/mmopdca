# =========================================================
# ASSIST_KEY: 【core/schemas/plan_schemas.py】
# =========================================================
#
# 【概要】
#   Plan エンドポイントで使う Pydantic モデル群
#   - PlanCreateRequest : 作成リクエスト (id は任意)
#   - PlanResponse      : 作成後に返す共通レスポンス
# ---------------------------------------------------------

from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class PlanCreateRequest(BaseModel):
    """
    Plan 作成リクエスト。

    `id` を省略した場合はルーター側で UUID を自動発番する。
    """

    id: Optional[str] = Field(
        default=None,
        description="Plan ID（省略可。サーバが自動採番）",
        examples=["plan_0001", "3fa85f64-5717-4562-b3fc-2c963f66afa6"],
    )
    symbol: str = Field(..., description="ティッカーシンボル", examples=["AAPL"])
    start: date = Field(..., description="学習開始日 (ISO-8601)")
    end: date = Field(..., description="学習終了日 (ISO-8601)")


class PlanResponse(BaseModel):
    """作成／取得共通で返す最小レスポンス"""

    id: str
    symbol: str
    start: date
    end: date
    created_at: str
