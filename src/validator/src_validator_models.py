from pydantic import BaseModel, Field, root_validator
from typing import List, Literal

class Baseline(BaseModel):
    lookback_days: int = Field(..., ge=1, description="自動抽出 or 明示指定")
    horizon_days: int = Field(7, ge=1, le=90)
    strategy: Literal["mean", "median", "last"] = "mean"

class MovingAverageParams(BaseModel):
    window: int = Field(..., ge=1)
    normalize: bool = Field(True)

class ExponentialSmoothingParams(BaseModel):
    alpha: float = Field(..., ge=0.0, le=1.0)
    adjust: bool = Field(False)

class FeatureBlock(BaseModel):
    name: Literal["MovingAverage", "ExponentialSmoothing"]
    params: dict  # 詳細はバリデータ側でチェック

class PlanSchema(BaseModel):
    version: Literal["plan_v1"]
    baseline: Baseline
    row_count: int = Field(..., ge=40, le=10000)
    feature_blocks: List[FeatureBlock]

    @root_validator(pre=True)
    def apply_defaults_and_auto_fill(cls, values):
        # lookback_days / row_count の自動補完ロジックをここに書く
        return values
