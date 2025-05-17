# ─── core/schemas/prediction.py ─────────────────────────────────────────
from __future__ import annotations

import uuid
from datetime import datetime
from typing import List

from pydantic import BaseModel, Field

__all__ = ["PredictionRecord", "PredictionArtifact"]


class PredictionRecord(BaseModel):
    """
    1 本の予測レコード
    """

    symbol: str
    ts: datetime
    horizon: int
    y_true: float
    y_pred: float
    model_id: str


class PredictionArtifact(BaseModel):
    """
    予測ジョブ 1 回分の “成果物”。
    plan_id / run_id はテストで省略できるようデフォルトを自動生成にする。
    """

    plan_id: str | None = Field(
        default_factory=lambda: f"plan-{uuid.uuid4().hex[:8]}"
    )
    run_id: str | None = Field(
        default_factory=lambda: f"run-{uuid.uuid4().hex[:8]}"
    )
    records: List[PredictionRecord]
