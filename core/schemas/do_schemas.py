# =========================================================
# core/schemas/do_schemas.py
# ---------------------------------------------------------
# ● Do-phase Pydantic v2 schemas
#     ├─ DoCreateRequest : 「Do ジョブを走らせてほしい」リクエスト
#     └─ DoResponse      : ジョブの実行状態・結果を返すレスポンス
# ---------------------------------------------------------
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, Annotated
from pydantic import BaseModel, Field, HttpUrl

# ---------------------------------------------------------------------
# サポート: テクニカル指標パラメータ
# ---------------------------------------------------------------------


class IndicatorParam(BaseModel):
    """
    追加で計算したいテクニカル指標のパラメータ

    **MVP では SMA のみを想定**。
    """

    name: Literal["SMA"] = Field(..., description="指標名")
    window: int = Field(
        5,
        ge=1,
        le=200,
        description="計算ウィンドウ（日 / バー数）",
        examples=[5, 20, 50],
    )


# ---------------------------------------------------------------------
# 入力スキーマ ── DoCreateRequest
# ---------------------------------------------------------------------


class DoCreateRequest(BaseModel):
    """
    Do フェーズ実行のリクエスト。

    - すべて任意。未指定なら Plan 側の値を継承。
    - **`run_no` が必須**（旧フィールド `seq` が来たらフォールバック）。
    """

    # ---- Plan 設定オーバーライド ----
    symbol: Optional[str] = Field(
        default=None,
        description="ティッカーシンボル（例: AAPL, ETH-USD）",
        examples=["AAPL"],
    )
    start: Optional[str] = Field(
        default=None,
        description="学習開始日 (ISO-8601)",
        examples=["2025-01-01"],
    )
    end: Optional[str] = Field(
        default=None,
        description="学習終了日 (ISO-8601)",
        examples=["2025-12-31"],
    )
    indicators: Optional[
        Annotated[list[IndicatorParam], Field(min_length=0)]
    ] = Field(default=None, description="追加テクニカル指標リスト")

    # ---- 実行メタ ----
    run_no: Optional[int] = Field(
        default=None,
        ge=1,
        description="必須。1,2,3… と連番を渡す（未指定なら seq を流用）",
        examples=[1, 2],
    )
    seq: Optional[int] = Field(
        default=None,
        ge=1,
        description="旧フィールド（残っていれば run_no に流用）",
        examples=[1, 2],
    )
    run_tag: Optional[str] = Field(
        default=None,
        max_length=32,
        description="自由ラベル（A/B テストや cron 名など）",
        examples=["baseline", "weekly-run"],
    )

 # ★★★ ここが追加 ★★★
    run_no: Optional[int] = Field(
        default=None,
        ge=1,
        description="executor 互換の連番（指定しなければ seq→1 を流用）",
        examples=[1],
    )
    
    # --------------------------------------------------
    # バリデーション: seq → run_no フォールバック
    # --------------------------------------------------
    def model_post_init(self, __context: Any) -> None:  # noqa: D401
        if self.run_no is None and self.seq is not None:
            object.__setattr__(self, "run_no", self.seq)


# ---------------------------------------------------------------------
# 出力スキーマ ── DoResponse
# ---------------------------------------------------------------------


class DoResponse(BaseModel):
    """
    Do ジョブの状態および結果を返すレスポンス。

    `status` 遷移: **PENDING → RUNNING → (DONE | FAILED)**
    """

    # ----- 識別子 -----
    do_id: str = Field(..., description="Do 実行 ID (do-xxxx 形式)")
    plan_id: str = Field(..., description="紐づく Plan ID")

    # ----- 実行メタ (エコーバック) -----
    seq: int = Field(
        1,
        ge=1,
        description="DoCreateRequest.run_no のエコーバック（互換のため 'seq' に格納）",
    )
    run_tag: Optional[str] = Field(
        default=None,
        description="DoCreateRequest.run_tag のエコーバック",
    )

    # ----- 実行状態 -----
    status: Literal["PENDING", "RUNNING", "DONE", "FAILED"] = Field(
        ..., description="ジョブ状態"
    )

    # ----- 実行結果 -----
    result: Optional[Dict[str, Any]] = Field(
        default=None,
        description=(
            "ジョブ完了時の任意ペイロード\n"
            "  • DONE   : メトリクスや artefact URI など\n"
            "  • FAILED : {'error': '...'} など"
        ),
    )

    # ----- 付加情報（将来拡張）-----
    dashboard_url: Optional[HttpUrl] = Field(
        default=None,
        description="Superset 等に自動生成された可視化 URL（任意）",
    )
