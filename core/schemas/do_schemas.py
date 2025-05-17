from __future__ import annotations
from datetime import date
from enum import Enum
from typing import Any, Dict, List, Optional, Annotated

from pydantic import BaseModel, Field, HttpUrl


# ───────────────────────────────────────
# テクニカル指標
# ───────────────────────────────────────
class IndicatorParam(BaseModel):
    name: Annotated[str, Field(description="指標名", examples=["SMA"])] = "SMA"
    window: Annotated[int, Field(ge=1, le=200, examples=[5, 20, 50])] = 5


# ───────────────────────────────────────
# Do ジョブ状態
# ───────────────────────────────────────
class DoStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    DONE = "DONE"
    FAILED = "FAILED"


# ───────────────────────────────────────
# 入力: DoCreateRequest
# ───────────────────────────────────────
class DoCreateRequest(BaseModel):
    symbol: Optional[str] = Field(None, examples=["AAPL"])
    start: Optional[date] = None
    end:   Optional[date] = None
    indicators: Optional[Annotated[List[IndicatorParam], Field(min_length=0)]] = None
    run_no: Optional[int] = Field(None, ge=1, examples=[1, 2])
    seq:    Optional[int] = Field(None, ge=1)              # deprecated
    run_tag: Optional[str] = Field(None, max_length=32)

    def model_post_init(self, __ctx):      # seq -> run_no 移行
        if self.run_no is None and self.seq:
            object.__setattr__(self, "run_no", self.seq)


# ───────────────────────────────────────
# 出力: DoResponse
# ───────────────────────────────────────
class DoResponse(BaseModel):
    do_id: str
    plan_id: str
    seq: int
    run_tag: Optional[str] = None
    status: DoStatus
    result: Optional[Dict[str, Any]] = None
    artifact_uri: Optional[str] = None
    dashboard_url: Optional[HttpUrl] = None


# ────────────────────────────────────────────────
# パッケージ公開シンボル
# ────────────────────────────────────────────────
__all__ = [
    "IndicatorParam",
    "DoStatus",
    "DoCreateRequest",
    "DoResponse",
]