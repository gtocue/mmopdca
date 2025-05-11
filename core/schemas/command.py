# =========================================================
# ASSIST_KEY: 【core/schemas/command.py】
# =========================================================
#
# 【概要】
#   Plan（＝命令書）エンドポイントで用いる Pydantic v2 モデル。
#     • PlanCreateRequest … 新規登録リクエスト用
#     • PlanCommand       … DB/レスポンス用（created_at 付き）
#
# 【連携先】
#   - api/routers/plan_api.py
#   - core.repository.*     （保存実装）
#
# 【ルール】
#   1) すべて ISO-8601 / UTC を採用（created_at）
#   2) 型安全重視・ハードコードは “TODO” コメントで明示
#   3) このファイルはユニット全体を返す――スニペット不可
# ---------------------------------------------------------

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field


# --------------------------------------------------
# リクエスト: PlanCreateRequest
# --------------------------------------------------
class PlanCreateRequest(BaseModel):
    """
    Plan 新規登録リクエスト。

    * `id` を省略すればサーバ側（router）が自動採番。
    """

    id: Optional[str] = Field(
        default=None,
        description="Plan ID（省略でサーバ自動採番）",
        examples=["plan_0001", "3fa85f64-5717-4562-b3fc-2c963f66afa6"],
    )
    symbol: str = Field(..., description="ティッカーシンボル", examples=["AAPL"])
    start: date = Field(
        ..., description="学習開始日 (YYYY-MM-DD)", examples=["2024-01-01"]
    )
    end: date = Field(
        ..., description="学習終了日 (YYYY-MM-DD)", examples=["2024-12-31"]
    )


# --------------------------------------------------
# レスポンス/保存形: PlanCommand
# --------------------------------------------------
class PlanCommand(PlanCreateRequest):
    """
    DB 保存・レスポンス共用モデル。（created_at を追加）
    """

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc),
        description="登録日時 (UTC, ISO-8601)",
        examples=["2025-04-29T10:00:00Z"],
    )
