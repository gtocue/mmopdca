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

from pydantic import BaseModel


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
    複数の PredictionRecord をまとめたアーティファクト。
    plan_id/run_id と一緒に返却・保存されます。
    """

    plan_id: str
    run_id: str
    records: List[PredictionRecord]
