# =====================================================================
# ASSIST_KEY: 【api/main_api.py】  – FastAPI エントリポイント (MVP)
# =====================================================================
#
# mmopdca “MVP ルータ集約サービス”。各フェーズ + 監視ルータを 1 つの
# FastAPI インスタンスにマウントし、Swagger / Redoc を公開する。
#
# 依存ルータ:
#   • api/routers/plan_api.py       – Plan CRUD
#   • api/routers/plan_dsl_api.py   – Plan DSL
#   • api/routers/do_api.py         – Do (Celery enqueue)
#   • api/routers/check_api.py      – Check (Parquet 評価)
#   • api/routers/act_api.py        – Act   (未実装なら 501 Stub)
#   • api/routers/metrics.py        – Prometheus 指標 (任意)
#
# 追加・変更ポリシ:
#   1) **破壊的変更は禁止**（追加のみ可）
#   2) /health は include_in_schema=False でドキュメント非公開
# ---------------------------------------------------------------------
from __future__ import annotations

import logging
from importlib import import_module
from typing import List

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())   # *.env を再帰探索して環境変数に投入

from fastapi import APIRouter, FastAPI

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Helper : 任意ルータを安全に import（無ければ 501 Stub で代替）
# ----------------------------------------------------------------------
def _import_optional(path: str, prefix: str, tag: str) -> APIRouter:
    """
    任意ルータを安全に import。ModuleNotFoundError だけでなく
    **FileNotFoundError も握って 501 Stub** にフォールバックする。
    """
    try:
        module = import_module(path)
        return getattr(module, "router")
    except (ModuleNotFoundError, FileNotFoundError):  # 👈 追加
        logger.warning("[main_api] %s unavailable – 501 stub で代替", path)
        stub = APIRouter(prefix=prefix, tags=[tag])

        @stub.get("/", status_code=501)
        def _stub() -> dict[str, str]:
            return {"detail": f"{tag.capitalize()} phase not implemented yet"}

        return stub


# ----------------------------------------------------------------------
# Core Routers（必須）
# ----------------------------------------------------------------------
from api.routers.plan_api import router as plan_router          # type: ignore
from api.routers.plan_dsl_api import router as plan_dsl_router  # type: ignore
from api.routers.do_api import router as do_router              # type: ignore

# ----------------------------------------------------------------------
# Optional Routers（存在しなければ stub）
# ----------------------------------------------------------------------
check_router   = _import_optional("api.routers.check_api", "/check", "check")
act_router     = _import_optional("api.routers.act_api", "/act", "act")
metrics_router = _import_optional("api.routers.metrics", "/metrics", "metrics")

# ----------------------------------------------------------------------
# FastAPI Application
# ----------------------------------------------------------------------
app = FastAPI(
    title="mmopdca MVP",
    version="0.2.0",
    description="Command-DSL-driven forecasting micro-service (Plan / Do / Check)",
    contact={"name": "gtocue", "email": "gtocue510@gmail.com"},
)

# ----------------------------------------------------------------------
# Meta / Utility Router
# ----------------------------------------------------------------------
meta_router = APIRouter(tags=["meta"])


@meta_router.get("/health", include_in_schema=False)
def health() -> dict[str, str]:
    """Liveness / Readiness Probe for k8s / Docker HEALTHCHECK."""
    return {"status": "ok"}


app.include_router(meta_router)

# ----------------------------------------------------------------------
# Business Routers
# ----------------------------------------------------------------------
app.include_router(plan_router)        # /plan
app.include_router(plan_dsl_router)    # /plan-dsl
app.include_router(do_router)          # /do   (202 Accepted & Celery run)
app.include_router(check_router)       # /check
app.include_router(act_router)         # /act
app.include_router(metrics_router)     # /metrics

# ----------------------------------------------------------------------
# NOTE:
#   • 認証 / CORS / 共通エラーハンドラは別ユニットで追加予定
#   • /metrics/* は Prometheus Exporter など外部用途でも再利用
# ----------------------------------------------------------------------
