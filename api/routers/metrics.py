# =========================================================
# ASSIST_KEY: 【api/routers/metrics.py】
# =========================================================
#
# 【概要】
#   Metrics Router ― Prometheus メトリクスを REST 経由で提供。
#   • GET /metrics/{name}        : 単一値（TTL 30 s キャッシュ）
#   • GET /metrics               : カタログ一覧 (name, unit, class)
#
# 【主な役割】
#   - signal_catalog.yml を読み込み、expr / slo / unit を返す
#   - utils.promsdk.instant_query を呼び出し、値を取得
#   - ValueError / PromQueryError を HTTP へ変換
#
# 【連携先・依存関係】
#   - utils/promsdk.py  : instant_query()
#   - metrics/signal_catalog.yml : 指標定義
#
# 【ルール遵守】
#   1) .yml を毎リクエスト再読み込みしない → 初回だけ読んでバージョンメモ
#   2) 例外は HTTPException にマッピング
#   3) 本ヘッダーは残す
# ---------------------------------------------------------

from __future__ import annotations

import logging
import pathlib
import time
from typing import Any, Dict, Literal

import yaml
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from utils.promsdk import PromQueryError, instant_query

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/metrics", tags=["metrics"])

# ────────────────────────────────
# YAML カタログ読み込み (一度だけ)
# ────────────────────────────────

_CATALOG_PATH = pathlib.Path("metrics/signal_catalog.yml")
if not _CATALOG_PATH.exists():
    raise FileNotFoundError("metrics/signal_catalog.yml が見つかりません")

with _CATALOG_PATH.open("r", encoding="utf-8") as fp:
    _CATALOG: Dict[str, Dict[str, Any]] = yaml.safe_load(fp) or {}

logger.info("[MetricsRouter] loaded %d metrics from catalog", len(_CATALOG))

# ────────────────────────────────
# Pydantic schemas
# ────────────────────────────────

Priority = Literal["S", "A", "B"]


class MetricMeta(BaseModel):
    name: str
    unit: str | None = None
    slo: float | None = None
    priority: Priority = Field(alias="class")


class MetricValue(MetricMeta):
    ts: int
    value: float


# ────────────────────────────────
# Helpers
# ────────────────────────────────


def _get_meta(name: str) -> Dict[str, Any]:
    spec = _CATALOG.get(name)
    if not spec:
        raise HTTPException(404, detail=f"Metric '{name}' not found")
    return spec


# ────────────────────────────────
# Routes
# ────────────────────────────────


@router.get("/{name}", response_model=MetricValue, summary="Get instant metric value")
def get_metric_value(name: str) -> MetricValue:  # noqa: D401
    spec = _get_meta(name)
    try:
        val = instant_query(spec["expr"])
    except PromQueryError as exc:  # pragma: no cover
        raise HTTPException(502, detail=exc.detail) from exc
    return MetricValue(
        name=name,
        value=val,
        ts=int(time.time()),
        **{k: spec.get(k) for k in ("unit", "slo", "class")},
    )


@router.get("/", response_model=list[MetricMeta], summary="List metric catalog")
def list_metrics() -> list[MetricMeta]:
    return [MetricMeta(name=name, **spec) for name, spec in _CATALOG.items()]
