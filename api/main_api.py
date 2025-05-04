# =====================================================================
# ASSIST_KEY: 【api/main_api.py】  ─ FastAPI エントリポイント (MVP)
# =====================================================================
#
# mmopdca “MVP ルータ集約サービス”。各フェーズ ＋ 監視ルータ を 1 つの
# FastAPI インスタンスにマウントし、Swagger / Redoc を公開する。
#
# 依存:
#   • api/routers/plan_api.py      – Plan CRUD
#   • api/routers/plan_dsl_api.py  – Plan DSL (YAML/JSON) CRUD
#   • api/routers/do_api.py        – Do (Celery enqueue)
#   • api/routers/metrics.py       – Prometheus 指標 REST ★ NEW ★
#   • api/routers/check_api.py     – Check (optional)
#   • api/routers/act_api.py       – Act   (optional)
#
# 追加・変更ポリシ:
#   1) **破壊的変更は禁止**（追加のみ可）
#   2) /health は include_in_schema=False でドキュメント非公開
# ---------------------------------------------------------------------
from __future__ import annotations

import logging

from fastapi import APIRouter, FastAPI

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Core Routers ― 実装必須
# ----------------------------------------------------------------------
from api.routers.plan_api import router as plan_router
from api.routers.plan_dsl_api import router as plan_dsl_router
from api.routers.do_api import router as do_router
from api.routers.metrics import router as metrics_router  # ★ 追加

# ----------------------------------------------------------------------
# Optional Routers ― 無ければ 501 Stub を生成
# ----------------------------------------------------------------------

def _lazy_stub(prefix: str, tag: str) -> APIRouter:
    r = APIRouter(prefix=prefix, tags=[tag])

    @r.get("/", status_code=501)
    def _stub() -> dict[str, str]:
        return {"detail": f"{tag.capitalize()} phase not implemented yet"}

    return r


try:
    from api.routers.check_api import router as check_router  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    logger.warning("[main_api] check_api 未実装 – 501 stub で代替")
    check_router = _lazy_stub("/check", "check")

try:
    from api.routers.act_api import router as act_router  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    logger.warning("[main_api] act_api 未実装 – 501 stub で代替")
    act_router = _lazy_stub("/act", "act")

# ----------------------------------------------------------------------
# FastAPI Application
# ----------------------------------------------------------------------
app = FastAPI(
    title="mmopdca MVP",
    version="0.2.0",  # 監視 UI 追加
    description="Command‑DSL‑driven forecasting micro‑service (Plan / Do / Metrics)",
    contact={"name": "gtocue", "email": "gtocue510@gmail.com"},
)

# ----------------------------------------------------------------------
# Meta / Utility Endpoints
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
app.include_router(do_router)          # /do   (202 Accepted & BG run)
app.include_router(metrics_router)     # /metrics
app.include_router(check_router)       # /check (501 stub 可能性あり)
app.include_router(act_router)         # /act   (501 stub 可能性あり)

# ----------------------------------------------------------------------
# NOTE:
#   • 認証 / CORS / 共通エラーハンドラは別ユニットで追加する方針
#   • /metrics/* は UI だけでなく外部 Exporter でも再利用可能。
# ----------------------------------------------------------------------
