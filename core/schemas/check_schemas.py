# =========================================================
# ASSIST_KEY: このファイルは【core/schemas/check_schemas.py】に位置するユニットです
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
# 【ルール遵守】 … (共通ガイドライン参照)
# ---------------------------------------------------------

from __future__ import annotations

from datetime import datetime
from typing import Dict, Union

from pydantic import BaseModel, Field


class CheckReport(BaseModel):
    """
    r2・threshold・pass/failed など可変キーを許容する緩いモデル
    """
    r2: float = Field(..., ge=-1.0, le=1.0, description="決定係数")
    threshold: float = Field(..., ge=-1.0, le=1.0, description="合格ライン")
    passed: bool = Field(..., description="閾値をクリアしたら True")
    # NOTE: 今後 rmse, mape など追加する場合はここに列挙 or Extra="allow"


class CheckResult(BaseModel):
    """
    /check エンドポイントのレスポンス & ストレージフォーマット
    """
    id: str = Field(..., description="check-xxxx 形式の一意 ID")
    do_id: str = Field(..., description="評価対象の Do ID")
    created_at: datetime = Field(..., description="UTC ISO8601")
    report: Dict[str, Union[int, float, str, bool]] | CheckReport = Field(
        ..., description="メトリクス JSON"
    )
