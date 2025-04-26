# ASSIST_KEY: このファイルは【core/schemas/do_schemas.py】に位置するユニットです.
#
# 【概要】
#   Do フェーズで使う Pydantic スキーマ群。
#   - DoCreateRequest : Plan 実行指示 & 追加パラメータ
#   - DoResponse      : Do 実行結果 (API 返却用)
#
# ---------------------------------------------------------

from __future__ import annotations

from typing import Any, Dict, List, Literal

from pydantic import BaseModel, Field, conlist


# ---------- 入力 ----------
class IndicatorParam(BaseModel):
    name: Literal["SMA"] = Field(..., description="インジケータ名 (現状 SMA のみ)")
    window: int = Field(5, ge=1, le=200, description="計算ウィンドウ長")


class DoCreateRequest(BaseModel):
    symbol: str = Field(..., examples=["AAPL"])
    start: str = Field(..., examples=["2024-01-01"])
    end: str = Field(..., examples=["2024-12-31"])
    indicators: conlist(IndicatorParam, min_length=0) = Field(
        default_factory=list, description="追加で計算したい指標"
    )


# ---------- 出力 ----------
class DoResponse(BaseModel):
    do_id: str
    plan_id: str
    status: Literal["DONE", "FAILED"]
    result: Dict[str, Any]
