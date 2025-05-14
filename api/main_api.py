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
#   • api/routers/check_api.py      – Check (評価)
#   • api/routers/act_api.py        – Act   (未実装なら 501 Stub)
#   • api/routers/metrics.py        – 指標 CRUD API (任意)
#   • api/routers/metrics_exporter.py – Prometheus Exporter (任意)
#
# ポリシ
#   1) 破壊的変更は禁止（追加のみ可）
#   2) /healthz は include_in_schema=False でドキュメント非公開
# ---------------------------------------------------------------------
from __future__ import annotations

import logging
from importlib import import_module
from typing import Final

from dotenv import load_dotenv, find_dotenv
from fastapi import APIRouter, FastAPI

# ─────────────────────────── env / logger
load_dotenv(find_dotenv())  # *.env を再帰探索して環境変数に投入
logger: Final = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# ----------------------------------------------------------------------
# Celery タスクモジュールを必ずインポート（Eager モードでも登録されるよう）
# ----------------------------------------------------------------------
import core.tasks.do_tasks  # 追加: run_do_task を登録

# ----------------------------------------------------------------------
# Core Routers（必須）
# ----------------------------------------------------------------------
from api.routers.plan_api import router as plan_router  # type: ignore
from api.routers.plan_dsl_api import router as plan_dsl_router  # type: ignore
from api.routers.do_api import router as do_router  # type: ignore
from api.routers.check_api import router as check_router  # type: ignore


# ----------------------------------------------------------------------
# Optional Routers（存在しなければ stub）
# ----------------------------------------------------------------------
def _import_optional(path: str, prefix: str, tag: str) -> APIRouter:
    """
    存在しないルータは 501 Stub で代替するヘルパ。

    Parameters
    ----------
    path : str
        importlib.import_module 互換のモジュールパス
    prefix : str
        APIRouter prefix
    tag : str
        ドキュメントタグ
    """
    try:
        module = import_module(path)
        return getattr(module, "router")
    except (ModuleNotFoundError, FileNotFoundError):
        logger.warning("[main_api] %s unavailable – 501 stub で代替", path)
        stub = APIRouter(prefix=prefix, tags=[tag])

        @stub.get("/", status_code=501)
        def _stub() -> dict[str, str]:
            return {"detail": f"{tag.capitalize()} phase not implemented yet"}

        return stub


act_router = _import_optional("api.routers.act_api", "/act", "act")
metrics_router = _import_optional("api.routers.metrics", "/metrics-api", "metrics")

# Prometheus Exporter (/metrics) – サブアプリ扱い
try:
    from api.routers.metrics_exporter import create_metrics_exporter

    exporter_app = create_metrics_exporter()
except (ModuleNotFoundError, FileNotFoundError):
    exporter_app = None
    logger.warning("[main_api] metrics_exporter unavailable – skip mount")

# ----------------------------------------------------------------------
# Legacy サブアプリ: 旧 HTML/ドキュメントルートを /v1 にまとめる
# ----------------------------------------------------------------------
legacy_app = FastAPI(
    title="mmopdca Legacy",
    version="0.3.0",
    description="Legacy HTML UI & Swagger",
    openapi_prefix="/v1",
    docs_url="/v1/docs",
    redoc_url="/v1/redoc",
)

# Health / Meta for legacy (例として同じ health)
from api.routes.health import router as health_router  # type: ignore
legacy_app.include_router(health_router)

# 旧 UI 用ルータ（存在すれば）
try:
    from api.routers.ui import router as ui_router
    legacy_app.include_router(ui_router)
except (ModuleNotFoundError, FileNotFoundError):
    logger.info("[main_api] ui router not found – skipping legacy UI mount")


# ----------------------------------------------------------------------
# FastAPI Application (API-Only)
# ----------------------------------------------------------------------
app = FastAPI(
    title="mmopdca API",
    version="0.4.0",
    description="Command-DSL-driven forecasting micro-service API only",
    contact={"name": "gtocue", "email": "gtocue510@gmail.com"},
)

# ----------------------------------------------------------------------
# Health / Meta Routers
# ----------------------------------------------------------------------
app.include_router(health_router)  # /healthz
meta_router = APIRouter(prefix="/meta", tags=["meta"])
app.include_router(meta_router)

# ----------------------------------------------------------------------
# Business Routers
# ----------------------------------------------------------------------
app.include_router(plan_router)      # /plan
app.include_router(plan_dsl_router) # /plan-dsl
app.include_router(do_router)       # /do
app.include_router(check_router)    # /check
app.include_router(act_router)      # /act
app.include_router(metrics_router)  # /metrics-api

# Prometheus Exporter (/metrics)
if exporter_app:
    app.mount("/metrics", exporter_app, name="metrics-exporter")

# ----------------------------------------------------------------------
# マウント: Legacy を /v1 に配置
# ----------------------------------------------------------------------
app.mount("/v1", legacy_app)

# ----------------------------------------------------------------------
# NOTE:
#   • 認証 / CORS / 共通エラーハンドラは別ユニットで追加予定
#   • /metrics (exporter) と /metrics-api (CRUD) を分離
# ----------------------------------------------------------------------
