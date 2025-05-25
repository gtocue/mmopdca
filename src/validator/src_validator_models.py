from __future__ import annotations

from pydantic import BaseModel, Field, root_validator
from typing import List, Literal, Optional

class Baseline(BaseModel):
    lookback_days: Optional[int] = Field(
        None,
        ge=1,
        description="自動抽出 or 明示指定"
    )
    horizon_days: int = Field(
        7,
        ge=1,
        le=90,
        description="予測先の日数（省略時7日）"
    )
    strategy: Literal["mean", "median", "last"] = Field(
        "mean",
        description="baseline計算方法（mean/median/last）"
    )

class MovingAverageParams(BaseModel):
    window: int = Field(
        ...,
        ge=1,
        description="移動平均の窓サイズ（日数）"
    )
    normalize: bool = Field(
        True,
        description="Trueなら正規化を行う"
    )

class ExponentialSmoothingParams(BaseModel):
    alpha: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="平滑化係数 α（0〜1）"
    )
    adjust: bool = Field(
        False,
        description="Trueなら調整付き指数平滑法を適用"
    )

class FeatureBlock(BaseModel):
    name: Literal["MovingAverage", "ExponentialSmoothing"]
    params: dict  # 詳細はバリデータ側でチェック

class PlanSchema(BaseModel):
    version: Literal["plan_v1"] = Field(
        ...,
        description="スキーマバージョン"
    )
    baseline: Baseline
    row_count: int = Field(
        ...,
        ge=40,
        le=10000,
        description="提出データの行数（最低40行、最大10000行）"
    )
    feature_blocks: List[FeatureBlock]

    @root_validator(pre=True)
    def apply_defaults_and_auto_fill(cls, values: dict) -> dict:
        """
        lookback_days を自動補完する。
        - lookback_days がない場合はデフォルト30日を設定
        """
        baseline = values.get("baseline")
        if isinstance(baseline, dict):
            baseline.setdefault("lookback_days", 30)
            values["baseline"] = baseline
        return values
