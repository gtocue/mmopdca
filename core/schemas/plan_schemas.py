# =========================================================
# ASSIST_KEY: 【core/schemas/plan_schemas.py】
# =========================================================
#
# 【概要】
#   Plan エンドポイントで使う Pydantic モデル群
#   - PlanCreateRequest : 作成リクエスト (id は任意)
#   - PlanResponse      : 取得／作成後に返すレスポンス
#     └ legacy 互換のため **未知フィールドもそのまま保持** する
# ---------------------------------------------------------
from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


# ------------------------------------------------------------------
# POST /plan/ 用
# ------------------------------------------------------------------
class PlanCreateRequest(BaseModel):
    """
    Plan 作成リクエスト。

    * `id` を省略した場合はルーター側で UUID を自動採番。
    * `symbol / start / end` は旧 API 互換の最小セット。
    """

    id: Optional[str] = Field(
        default=None,
        description="Plan ID（省略可。サーバが自動採番）",
        examples=["plan_abcd1234", "3fa85f64-5717-4562-b3fc-2c963f66afa6"],
    )
    symbol: str = Field(..., description="メイン銘柄ティッカー", examples=["AAPL"])
    start: date = Field(..., description="学習開始日 (ISO-8601)")
    end: date = Field(..., description="学習終了日 (ISO-8601)")


# ------------------------------------------------------------------
# 共通レスポンス
#   extra="allow" にして DSL 本体 (data/dates/…) も保持
# ------------------------------------------------------------------
class PlanResponse(BaseModel):
    """
    Plan 取得／作成時に返す共通レスポンス。

    旧クライアント互換の最小キー (id / symbol / start / end / created_at)
    以外にも、DSL 全フィールドを残すため `extra="allow"`。
    """

    id: str
    symbol: str
    start: Optional[date] = None
    end: Optional[date]   = None
    created_at: str

    # ★ 未定義フィールドを許可してそのまま返す
    model_config = ConfigDict(extra="allow")  # Pydantic v2
    # Pydantic v1 系を使う場合は:
    # class Config:
    #     extra = "allow"
