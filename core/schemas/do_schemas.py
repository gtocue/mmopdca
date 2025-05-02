# =========================================================
# core/schemas/do_schemas.py
# ---------------------------------------------------------
#  Do-phase (「Do フェーズ」) の Pydantic v2 スキーマ定義
#
#   • DoStatus        : ジョブ状態列挙
#   • DoCreateRequest : 実行リクエスト（任意項目は Plan から継承）
#   • DoResponse      : 状態／結果レスポンス
# =========================================================
from __future__ import annotations

from datetime import date
from enum import Enum
from typing import Any, Dict, List, Optional, Annotated

from pydantic import BaseModel, Field, HttpUrl


# ----------------------------------------------------------------------
# 汎用: テクニカル指標パラメータ（MVP は SMA のみ想定）
# ----------------------------------------------------------------------
class IndicatorParam(BaseModel):
    """
    追加計算したいテクニカル指標パラメータ。

    *MVP* では `name="SMA"` だけを想定するが、後方互換を考慮して
    任意文字列を許容している。
    """

    name: Annotated[str, Field(description="指標名", examples=["SMA"])] = "SMA"
    window: Annotated[
        int,
        Field(
            ge=1,
            le=200,
            description="計算ウィンドウ（日／バー数）",
            examples=[5, 20, 50],
        ),
    ] = 5


# ----------------------------------------------------------------------
# Enum: Do ジョブ状態
# ----------------------------------------------------------------------
class DoStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    DONE    = "DONE"
    FAILED  = "FAILED"


# ----------------------------------------------------------------------
# 入力スキーマ: DoCreateRequest
# ----------------------------------------------------------------------
class DoCreateRequest(BaseModel):
    """
    Do フェーズ実行リクエスト。

    すべて **任意**。未指定項目は対応する Plan の値を継承する。
    """

    # ---- Plan 値のオーバーライド ------------------------------------
    symbol: Optional[str] = Field(
        default=None,
        description="ティッカー（例: AAPL, ETH-USD）",
        examples=["AAPL"],
    )
    start: Optional[date] = Field(
        default=None,
        description="学習開始日 (YYYY-MM-DD)",
        examples=["2025-01-01"],
    )
    end:   Optional[date] = Field(
        default=None,
        description="学習終了日 (YYYY-MM-DD)",
        examples=["2025-12-31"],
    )
    indicators: Optional[
        Annotated[List[IndicatorParam], Field(min_length=0)]
    ] = Field(
        default=None,
        description="追加テクニカル指標リスト（空 list で『追加なし』）",
    )

    # ---- 実行メタ ----------------------------------------------------
    run_no: Optional[int] = Field(
        default=None,
        ge=1,
        description="連番 (1,2,3 …)。未指定なら `seq` をフォールバック",
        examples=[1, 2],
    )
    seq: Optional[int] = Field(           # ← 旧フィールド (互換のため残置)
        default=None,
        ge=1,
        description="※ deprecated – `run_no` に自動コピーされる",
        examples=[1, 2],
    )
    run_tag: Optional[str] = Field(
        default=None,
        max_length=32,
        description="自由ラベル（A/B テスト名など）",
        examples=["baseline", "weekly-run"],
    )

    # ---- 後処理: 互換フォールバック ---------------------------------
    def model_post_init(self, __context: Any) -> None:     # noqa: D401
        # `seq` → `run_no` への移行をシームレスに
        if self.run_no is None and self.seq is not None:
            object.__setattr__(self, "run_no", self.seq)


# ----------------------------------------------------------------------
# 出力スキーマ: DoResponse
# ----------------------------------------------------------------------
class DoResponse(BaseModel):
    """
    Do ジョブの状態および結果レスポンス。

    `status` 遷移: **PENDING → RUNNING → (DONE | FAILED)**
    """

    # ----- 識別子 -----------------------------------------------------
    do_id:   str = Field(..., description="Do 実行 ID (`do-xxxx` 形式)")
    plan_id: str = Field(..., description="紐づく Plan ID")

    # ----- 実行メタ ---------------------------------------------------
    seq: Annotated[
        int,
        Field(
            ge=1,
            description="DoCreateRequest.run_no のエコーバック（互換: 'seq'）",
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


# 公開シンボル
__all__ = ["DoStatus", "DoCreateRequest", "DoResponse"]
