# =========================================================
# ASSIST_KEY: 【core/schemas/do_schemas.py】
# =========================================================
#
# Do-phase Pydantic v2 schemas
#   • DoStatus        : 状態列挙（PENDING / RUNNING / DONE / FAILED）
#   • DoCreateRequest : 「Do ジョブを走らせてほしい」リクエスト
#   • DoResponse      : ジョブの実行状態・結果を返すレスポンス
# ---------------------------------------------------------
from __future__ import annotations

from datetime import date
from enum import Enum
from typing import Any, Dict, Optional, Annotated, List

from pydantic import BaseModel, Field, HttpUrl


# ----------------------------------------------------------------------
# 汎用: テクニカル指標パラメータ
# ----------------------------------------------------------------------
class IndicatorParam(BaseModel):
    """
    追加で計算したいテクニカル指標のパラメータ

    **MVP では SMA だけ想定**。後方互換のため `name` は Literal。
    """

    name: Annotated[str, Field(description="指標名", examples=["SMA"])] = "SMA"
    window: Annotated[
        int,
        Field(
            ge=1,
            le=200,
            description="計算ウィンドウ（日 / バー数）",
            examples=[5, 20, 50],
        ),
    ] = 5


# ----------------------------------------------------------------------
# Enum: DoStatus
# ----------------------------------------------------------------------
class DoStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    DONE = "DONE"
    FAILED = "FAILED"


# ----------------------------------------------------------------------
# 入力スキーマ ── DoCreateRequest
# ----------------------------------------------------------------------
class DoCreateRequest(BaseModel):
    """
    Do フェーズ実行のリクエスト。

    すべて任意。未指定なら Plan 側の値を継承。
    """

    # ---- Plan オーバーライド (optional) ----------------------------
    symbol: Optional[str] = Field(
        default=None,
        description="ティッカーシンボル（例: AAPL, ETH-USD）",
        examples=["AAPL"],
    )
    start: Optional[date] = Field(
        default=None,
        description="学習開始日 (ISO-8601)",
        examples=["2025-01-01"],
    )
    end: Optional[date] = Field(
        default=None,
        description="学習終了日 (ISO-8601)",
        examples=["2025-12-31"],
    )
    indicators: Optional[
        Annotated[List[IndicatorParam], Field(min_length=0)]
    ] = Field(default=None, description="追加テクニカル指標リスト")

    # ---- 実行メタ ----------------------------------------------------
    run_no: Optional[int] = Field(
        default=None,
        ge=1,
        description="連番 (1,2,3…)。未指定なら deprecated `seq` からフォールバック",
        examples=[1, 2],
    )
    seq: Optional[int] = Field(
        default=None,
        ge=1,
        description="旧フィールド（残っていれば run_no にコピー）",
        examples=[1, 2],
    )
    run_tag: Optional[str] = Field(
        default=None,
        max_length=32,
        description="自由ラベル（A/B テストや cron 名など）",
        examples=["baseline", "weekly-run"],
    )

    # ----------------------------------------------------------------
    # post-init: 互換フォールバック
    # ----------------------------------------------------------------
    def model_post_init(self, __context: Any) -> None:  # noqa: D401
        # seq -> run_no 移行期サポート
        if self.run_no is None and self.seq is not None:
            object.__setattr__(self, "run_no", self.seq)


# ----------------------------------------------------------------------
# 出力スキーマ ── DoResponse
# ----------------------------------------------------------------------
class DoResponse(BaseModel):
    """
    Do ジョブの状態および結果を返すレスポンス。

    `status` 遷移: **PENDING → RUNNING → (DONE | FAILED)**
    """

    # ----- 識別子 -----------------------------------------------------
    do_id: str = Field(..., description="Do 実行 ID (do-xxxx 形式)")
    plan_id: str = Field(..., description="紐づく Plan ID")

    # ----- 実行メタ ---------------------------------------------------
    seq: Annotated[
        int,
        Field(
            ge=1,
            description="DoCreateRequest.run_no のエコーバック（互換のため 'seq'）",
        ),
    ]
    run_tag: Optional[str] = Field(
        default=None,
        description="DoCreateRequest.run_tag のエコーバック",
    )

    # ----- 実行状態 ---------------------------------------------------
    status: DoStatus = Field(..., description="ジョブ状態")

    # ----- 実行結果 ---------------------------------------------------
    result: Optional[Dict[str, Any]] = Field(
        default=None,
        description=(
            "ジョブ完了時の任意ペイロード\n"
            "  • DONE   : メトリクスや artefact URI など\n"
            "  • FAILED : {'error': '...'} など"
        ),
    )

    # ----- 付加情報 ---------------------------------------------------
    dashboard_url: Optional[HttpUrl] = Field(
        default=None,
        description="Superset 等に自動生成された可視化 URL（任意）",
    )


__all__ = ["DoStatus", "DoCreateRequest", "DoResponse"]
