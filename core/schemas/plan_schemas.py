"""
Plan エンドポイントで使う Pydantic v2 モデル群
* PlanCreateRequest : 作成リクエスト (id は任意)
* PlanResponse      : 取得／作成後レスポンス
"""
from __future__ import annotations

from datetime import date
from typing import Optional

import json
from pydantic import BaseModel, Field
from pydantic import __version__ as _pyd_version
try:
    from pydantic import ConfigDict as _Cfg
    _IS_PYDANTIC_V2 = not _pyd_version.startswith("1")
except Exception:  # pragma: no cover - pydantic v1
    _Cfg = None
    _IS_PYDANTIC_V2 = False


# POST /plan/ 用 --------------------------------------------------------
class PlanCreateRequest(BaseModel):
    """Plan 作成リクエスト。"""

    id: Optional[str] = Field(
        default=None,
        description="Plan ID（省略可。サーバが自動採番）",
        examples=["plan_abcd1234", "3fa85f64-…"],
    )
    symbol: str = Field(..., description="メイン銘柄ティッカー")
    start: date = Field(..., description="学習開始日 (ISO-8601)")
    end: date = Field(..., description="学習終了日 (ISO-8601)")


# 共通レスポンス --------------------------------------------------------
class PlanResponse(BaseModel):
    """Plan 取得／作成時の共通レスポンス。"""

    id: str
    symbol: str
    start: Optional[date] = None
    end: Optional[date] = None
    created_at: str

    # DSL フィールドもそのまま保持
    if _IS_PYDANTIC_V2 and _Cfg is not None:
        model_config = _Cfg(extra="allow")
    else:  # pragma: no cover - pydantic v1
        class Config:
            extra = "allow"

    def dict(self, *args, **kwargs):  # pragma: no cover - pydantic v1 compatibility
        data = super().dict(*args, **kwargs)
        extras = {k: v for k, v in self.__dict__.items() if k not in data}
        data.update(extras)
        return data

    def json(self, *args, **kwargs):  # pragma: no cover - pydantic v1 compatibility
        return json.dumps(self.dict(*args, **kwargs))

__all__ = ["PlanCreateRequest", "PlanResponse"]
