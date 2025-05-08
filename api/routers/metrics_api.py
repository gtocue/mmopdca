# =========================================================
# ASSIST_KEY: 【api/routers/metrics_api.py】
# =========================================================
#
# Metrics Router – Do / Check フェーズで算出した評価指標を
# CRUD + 絞り込み検索で提供し、Prometheus Exporter 連携の
# “入口” となるエンドポイント。
# ---------------------------------------------------------
# ・POST /metrics/{run_id}   : actual/pred を受け取り指標計算 → Upsert
# ・GET  /metrics/{run_id}   : 単一レコード取得
# ・GET  /metrics/           : 一覧（r2 フィルタ等の Query 対応）
# ・GET  /metrics/latest     : 最新 run_id のレコード取得     ← ★追加
# ---------------------------------------------------------
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from core.metrics.metrics_calc import calc_metrics
from core.repository.factory import get_repo

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/metrics", tags=["metrics"])

_metrics_repo = get_repo("metrics")  # Memory / Redis / FS など抽象化


# ---------------------------------------------------------------------- #
# Pydantic Schemas
# ---------------------------------------------------------------------- #
class MetricsPayload(BaseModel):
    """POST 時に受け取る Raw 配列（柔軟に許容）"""
    actual: list[float] = Field(..., description="実績値 (y)")
    pred: list[float] = Field(..., description="予測値 (ŷ)")


class MetricsRecord(BaseModel):
    """永続ストアに保存する正規化済みレコード"""
    run_id: str
    created_at: datetime
    r2: float
    mae: float
    rmse: float
    mape: float


# ---------------------------------------------------------------------- #
# helpers
# ---------------------------------------------------------------------- #
def _upsert_metrics(rec: MetricsRecord) -> None:
    """既存 run_id があっても上書き登録（Upsert）"""
    _metrics_repo.delete(rec.run_id)
    _metrics_repo.create(rec.run_id, rec.model_dump(mode="json"))


def _list_records() -> list[MetricsRecord]:
    """Repository → Pydantic へ変換（欠損はスキップ）"""
    return [
        MetricsRecord(**_metrics_repo.get(k))
        for k in _metrics_repo.keys()
        if _metrics_repo.get(k) is not None
    ]


# ---------------------------------------------------------------------- #
# POST /metrics/{run_id}
# ---------------------------------------------------------------------- #
@router.post(
    "/{run_id}",
    status_code=status.HTTP_201_CREATED,
    response_model=MetricsRecord,
    summary="評価指標を計算して保存（Upsert）",
)
def create_metrics(run_id: str, payload: MetricsPayload) -> MetricsRecord:
    # --- Validation -------------------------------------------------- #
    if len(payload.actual) != len(payload.pred):
        raise HTTPException(400, "Length mismatch between actual and pred")

    # --- Calc --------------------------------------------------------- #
    metrics = calc_metrics(payload.actual, payload.pred)

    rec = MetricsRecord(
        run_id=run_id,
        created_at=datetime.now(timezone.utc),
        **metrics,
    )
    _upsert_metrics(rec)

    logger.info("[MetricsAPI] Upsert run_id=%s r2=%.4f", run_id, rec.r2)
    return rec


# ---------------------------------------------------------------------- #
# GET /metrics/{run_id}
# ---------------------------------------------------------------------- #
@router.get(
    "/{run_id}",
    response_model=MetricsRecord,
    summary="単一メトリクスを取得",
)
def get_metrics(run_id: str) -> MetricsRecord:
    raw = _metrics_repo.get(run_id)
    if raw is None:
        raise HTTPException(404, "Metrics not found")
    return MetricsRecord(**raw)


# ---------------------------------------------------------------------- #
# GET /metrics/latest   ★追加
# ---------------------------------------------------------------------- #
@router.get(
    "/latest",
    response_model=MetricsRecord,
    summary="最新 run_id のメトリクスを取得",
)
def get_latest_metrics() -> MetricsRecord:
    if not _metrics_repo.keys():
        raise HTTPException(404, "Metrics repository is empty")
    latest_key = sorted(_metrics_repo.keys())[-1]
    return MetricsRecord(**_metrics_repo.get(latest_key))


# ---------------------------------------------------------------------- #
# GET /metrics/
# ---------------------------------------------------------------------- #
@router.get(
    "/",
    response_model=List[MetricsRecord],
    summary="メトリクス一覧（r²フィルタ付き）",
)
def list_metrics(
    min_r2: Optional[float] = Query(
        None, ge=0, le=1, description="絞り込み: r² ≥ min_r2"
    ),
) -> List[MetricsRecord]:
    metrics = _list_records()
    if min_r2 is not None:
        metrics = [m for m in metrics if m.r2 >= min_r2]
    # run_id 昇順で返す
    return sorted(metrics, key=lambda m: m.run_id)
