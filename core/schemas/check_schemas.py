# =========================================================
# ASSIST_KEY: 【core/schemas/check_schemas.py】に位置するユニットです
# =========================================================
#
# 【概要】
#   CheckResult スキーマ定義（Pydantic v2 系）
#   - Do フェーズの出力を評価したメトリクスを保持
#
# 【主な役割】
#   - CheckResult : /check API の I/O モデル
#
# 【連携先・依存関係】
#   - api/routers/check_api.py           … 生成 & 永続化
#   - core/repository/*                  … 任意バックエンド
#
# ---------------------------------------------------------
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Union

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


class CheckResult(BaseModel):
    """
    /check エンドポイントのレスポンス & ストレージフォーマット
    """

    id: str = Field(..., description="check-xxxx 形式の一意 ID")
    do_id: str = Field(..., description="評価対象の Do ID")
    created_at: datetime = Field(..., description="UTC ISO8601")

    # report は厳密モデル(CheckReport)でも任意 Dict でも可
    report: Dict[str, Union[int, float, str, bool]] | CheckReport = Field(
        ...,
        description="メトリクス JSON",
    )
