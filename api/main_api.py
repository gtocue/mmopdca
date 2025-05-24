# =====================================================================
# File: api/main_api.py  – FastAPI エントリポイント (MVP API-only)
# =====================================================================
#
# mmopdca “MVP ルータ集約サービス API-only”。
# 各フェーズのルータ群と /ws WebSocket ルートを 1 つの FastAPI インスタンスにマウントし、
# Swagger / Redoc を公開します。
#
# ポリシ
#   1) 破壊的変更は禁止（追加のみ可）
#   2) /healthz は include_in_schema=False でドキュメント非公開
# ---------------------------------------------------------------------

from __future__ import annotations

import logging
import os
from importlib import import_module
from typing import Final

from dotenv import load_dotenv, find_dotenv
from fastapi import (
    APIRouter,
    FastAPI,
    Depends,
    HTTPException,
    WebSocket,
)
from fastapi.security.api_key import APIKeyHeader
from fastapi.responses import StreamingResponse

# ─────────────────────────── env / logger
load_dotenv(find_dotenv())  # *.env を再帰探索して環境変数に投入
logger: Final = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# ----------------------------------------------------------------------
# Celery タスクモジュールを必ずインポート（Eager モードでも登録されるよう）
# ----------------------------------------------------------------------
import core.tasks.do_tasks  # type: ignore  # run_do_task を登録

# ----------------------------------------------------------------------
# API Key 認証設定
# ----------------------------------------------------------------------
API_KEY_NAME = "x-api-key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)


def verify_api_key(x_api_key: str = Depends(api_key_header)) -> None:
    """
    HTTP ヘッダ x-api-key による簡易認証。
    環境変数 API_KEY を設定している場合のみ有効化。
    """
    expected = os.getenv("API_KEY")
    if expected:
        if not x_api_key or x_api_key != expected:
            raise HTTPException(status_code=401, detail="Invalid or missing API Key")


# ----------------------------------------------------------------------
# Core Routers（必須）
# ----------------------------------------------------------------------
from api.routers.plan_api import router as plan_router  # type: ignore
from api.routers.plan_dsl_api import router as plan_dsl_router  # type: ignore
from api.routers.do_api import router as do_router  # type: ignore
from api.routers.check_api import router as check_router  # type: ignore


# ----------------------------------------------------------------------
# Optional Routers（存在しなければ 501 Stub）
# ----------------------------------------------------------------------

def _import_optional(path: str, prefix: str, tag: str) -> APIRouter:
    try:
        module = import_module(path)
        return getattr(module, "router")
    except (ModuleNotFoundError, FileNotFoundError):
        logger.warning("[main_api] %s unavailable – 501 stub", path)
        stub = APIRouter(prefix=prefix, tags=[tag])

        @stub.get("/", status_code=501)
        def _stub() -> dict[str, str]:
            return {"detail": f"{tag.capitalize()} phase not implemented yet"}

        return stub


act_router = _import_optional("api.routers.act_api", "/act", "act")
metrics_router = _import_optional("api.routers.metrics_api", "/metrics-api", "metrics")

# ----------------------------------------------------------------------
# Trace API (イベントストリーミング)
# ----------------------------------------------------------------------
from api.routers.events_api import router as events_router  # type: ignore

# ----------------------------------------------------------------------
# Prometheus Exporter (/metrics) – サブアプリ扱い
# ----------------------------------------------------------------------
try:
    from api.routers.metrics_exporter import create_metrics_exporter  # type: ignore

    exporter_app = create_metrics_exporter()
except (ModuleNotFoundError, FileNotFoundError):
    exporter_app = None
    logger.warning("[main_api] metrics_exporter unavailable – skip mount")

# ----------------------------------------------------------------------
# Legacy サブアプリ: 旧 HTML/UI ルートを /v1 にまとめる
# ----------------------------------------------------------------------
from api.routers.health import router as health_router  # type: ignore

legacy_app = FastAPI(
    title="mmopdca Legacy",
    version="0.3.0",
    description="Legacy HTML UI & Swagger",
    root_path="/v1",
    docs_url="/v1/docs",
    redoc_url="/v1/redoc",
)

# Health
legacy_app.include_router(health_router)

# 旧 UI 用ルータ（存在すれば）
try:
    from api.routers.ui import router as ui_router  # type: ignore

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

# Health / Meta Routers (認証必須)
app.include_router(
    health_router,
    dependencies=[Depends(verify_api_key)],
    include_in_schema=False,
)
meta_router = APIRouter(
    prefix="/meta",
    tags=["meta"],
    dependencies=[Depends(verify_api_key)],
)
app.include_router(meta_router)

# Business Routers (認証必須)
app.include_router(plan_router, dependencies=[Depends(verify_api_key)])
app.include_router(plan_dsl_router, dependencies=[Depends(verify_api_key)])
app.include_router(do_router, dependencies=[Depends(verify_api_key)])
app.include_router(check_router, dependencies=[Depends(verify_api_key)])
app.include_router(act_router, dependencies=[Depends(verify_api_key)])
app.include_router(metrics_router, dependencies=[Depends(verify_api_key)])
app.include_router(events_router, dependencies=[Depends(verify_api_key)])

# Prometheus Exporter (/metrics) – 認証不要
if exporter_app:
    app.mount("/metrics", exporter_app, name="metrics-exporter")


# ----------------------------------------------------------------------
# WebSocket 進捗ストリーミングエンドポイント
# ----------------------------------------------------------------------
@app.websocket("/ws/{run_id}")
async def ws_progress(
    websocket: WebSocket,
    run_id: str,
):
    """
    run_id に対応する進捗を 1 から 5 まで順番に JSON 送信後、切断します。
    x-api-key ヘッダを設定している場合は認証を行い、不正ならクローズ(1008)。
    """
    expected = os.getenv("API_KEY")
    if expected:
        key = websocket.headers.get(API_KEY_NAME)
        if not key or key != expected:
            await websocket.close(code=1008)
            return

    await websocket.accept()
    for i in range(1, 6):
        await websocket.send_json({"progress": i})
    await websocket.close()


# ----------------------------------------------------------------------
# マウント: Legacy を /v1 に配置
# ----------------------------------------------------------------------
app.mount("/v1", legacy_app)

# ----------------------------------------------------------------------
# NOTE:
#   • 認証 / CORS / 共通エラーハンドラは別ユニットで追加予定
#   • /metrics (exporter) と /metrics-api (CRUD) を分離
# ----------------------------------------------------------------------
