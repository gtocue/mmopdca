"""
core.schemas package  ― サブモジュールの公開クラスをフラットに再エクスポートする
===============================================================
pytest などから `from core.schemas import PlanCreateRequest` と書けるようにする。
"""

from __future__ import annotations

# ① 個別インポート
from .plan_schemas import PlanCreateRequest, PlanResponse
from .do_schemas import (
    IndicatorParam,
    DoStatus,
    DoCreateRequest,
    DoResponse,
)
from .prediction import PredictionRecord, PredictionArtifact

# ② __all__ を一元管理
__all__ = [
    # plan
    "PlanCreateRequest",
    "PlanResponse",
    # do
    "IndicatorParam",
    "DoStatus",
    "DoCreateRequest",
    "DoResponse",
    # prediction
    "PredictionRecord",
    "PredictionArtifact",
]
