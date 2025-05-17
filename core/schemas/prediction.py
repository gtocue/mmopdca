"""
PredictionArtifact / PredictionRecord ― 予測結果スキーマ
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import List

from pydantic import BaseModel, Field


class PredictionRecord(BaseModel):
    symbol: str
    ts: datetime
    horizon: int
    y_true: float
    y_pred: float
    model_id: str


class PredictionArtifact(BaseModel):
    plan_id: str = Field(default_factory=lambda: f"plan-{uuid.uuid4().hex[:8]}")
    run_id: str = Field(default_factory=lambda: f"run-{uuid.uuid4().hex[:8]}")
    records: List[PredictionRecord]


__all__ = ["PredictionRecord", "PredictionArtifact"]
