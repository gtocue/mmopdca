# =========================================================
# core/schemas/check_schemas.py
# =========================================================
#
# CheckResult スキーマ定義（Pydantic v2 系）
#   - Do フェーズの出力を評価したメトリクスを保持
#
# 修正ポイント:
#   report フィールドに None を許可する Optional 指定を追加
# ---------------------------------------------------------

from __future__ import annotations

from datetime import datetime
from typing import Dict, Union, Optional

from pydantic import BaseModel, Field, ConfigDict


class CheckReport(BaseModel):
    """
    可変キーを許容する緩いメトリクスモデル。
    デフォルト項目として r2 / threshold / passed を持ち、
    追加指標 (rmse, mape など) は extra="allow" で拡張可能。
    """

    r2: float = Field(..., ge=-1.0, le=1.0, description="決定係数")
    threshold: float = Field(..., ge=-1.0, le=1.0, description="合格ライン")
    passed: bool = Field(..., description="閾値をクリアしたら True")

    model_config = ConfigDict(extra="allow")  # ★ 追加指標を許容
    class Config:  # pragma: no cover - pydantic v1 fallback
        extra = "allow"


class CheckResult(BaseModel):
    """
    /check エンドポイントのレスポンス & ストレージフォーマット
    report はタスク未完了時に None を返すケースを考慮
    """

    id: str = Field(..., description="check-xxxx 形式の一意 ID")
    do_id: str = Field(..., description="評価対象の Do ID")
    created_at: datetime = Field(..., description="UTC ISO8601")

    # report は未完了時に None 許可
    report: Optional[Dict[str, Union[int, float, str, bool]] | CheckReport] = Field(
        None,
        description="メトリクス JSON (タスク完了前は None)",
    )

    model_config = ConfigDict(from_attributes=True)
    class Config:  # pragma: no cover - pydantic v1 fallback
        orm_mode = True
