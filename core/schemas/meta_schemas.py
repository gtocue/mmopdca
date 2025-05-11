# =========================================================
# ASSIST_KEY: このファイルは【core/schemas/meta_schemas.py】に位置するユニットです
# =========================================================
#
# 【概要】
#   このユニットは “MetaInfo スキーマ” として、
#   Plan→Do→Check を横断するメタデータ定義を提供します。
#
# 【主な役割】
#   - MetricSpec : 各評価指標と閾値のペア
#   - MetaInfo   : 1 サイクル (= run_id) 分の設定・閾値・期間を保持
#
# 【連携先・依存関係】
#   - core/common/io_utils.py         … save_meta() / load_meta()
#   - core/check/check_executor.py    … 指標閾値を参照
#
# 【ルール遵守】
#   1) 型安全 (Pydantic v2)・extra="forbid"
#   2) 破壊的変更時は docs/ARCH.md を更新
# ---------------------------------------------------------
from __future__ import annotations

from datetime import date, datetime
from typing import List

from pydantic import BaseModel, Field, ConfigDict


class MetricSpec(BaseModel):
    """
    評価指標と閾値のペア。
    """

    name: str = Field(..., examples=["mape", "rmse", "r2"])
    threshold: float = Field(
        ...,
        ge=0.0,
        description="この値以下（または r2 の場合は以上）で合格",
    )

    model_config = ConfigDict(extra="forbid")


class MetaInfo(BaseModel):
    """
    Plan/Do ランの設定値と、Check が参照する評価閾値をまとめたメタ。
    """

    plan_id: str
    run_id: str

    train_start: date
    train_end: date
    predict_horizon: int = Field(..., ge=1)

    metrics: List[MetricSpec] = Field(
        ...,
        description="Check フェーズが計算・判定すべき評価指標の一覧",
    )

    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(extra="forbid")


# 公開シンボル
__all__ = ["MetricSpec", "MetaInfo"]
