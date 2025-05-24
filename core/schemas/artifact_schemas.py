# core/schemas/artifact_schemas.py
# =====================================================================
# Pydantic モデル：予測結果アーティファクト
#
# • PredictionRecord   — 単一予測レコード
# • PredictionArtifact — 予測レコードの集合（plan_id/run_id付き）
# =====================================================================

from __future__ import annotations

from datetime import datetime
from typing import List

import uuid
from pydantic import BaseModel, Field

class PredictionRecord(BaseModel):
    """
    単一の予測結果レコードを表します。
    """

    symbol: str  # 銘柄またはプランID
    ts: datetime  # タイムスタンプ（UTC ISO8601）
    horizon: int  # 予測ホライゾン（日数）
    y_true: float  # 実績値
    y_pred: float  # 予測値
    model_id: str  # 使用モデルの識別子


class PredictionArtifact(BaseModel):
    """
    複数の ``PredictionRecord`` をまとめたアーティファクト。
    ``plan_id`` と ``run_id`` が指定されない場合は自動生成します。
    """

    plan_id: str = Field(default_factory=lambda: f"plan-{uuid.uuid4().hex[:8]}")
    run_id: str = Field(default_factory=lambda: f"run-{uuid.uuid4().hex[:8]}")
    records: List[PredictionRecord]

    # ------------------------------------------------------------------
    # Compatibility helpers for pydantic v1
    # ------------------------------------------------------------------
    def model_dump_json(self, **kwargs) -> str:
        """Return JSON representation (Pydantic v1 compat)."""
        if hasattr(super(), "model_dump_json"):
            return super().model_dump_json(**kwargs)
        return self.json(**kwargs)

    @classmethod
    def model_validate_json(cls, data: str, **kwargs) -> "PredictionArtifact":
        if hasattr(super(), "model_validate_json"):
            return super().model_validate_json(data, **kwargs)
        return cls.parse_raw(data, **kwargs)
