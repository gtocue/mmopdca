# ======================================================================
# ASSIST_KEY: 【api/main_api.py】  ─ FastAPI エントリポイント (MVP)
# ======================================================================
#
# mmopdca “MVP ルータ集約サービス”。各フェーズのルータを 1 つの
# FastAPI インスタンスにマウントし、Swagger UI を公開する。
#
# 依存:
#   • api/routers/plan_api.py      – Plan CRUD
#   • api/routers/plan_dsl_api.py  – Plan DSL (YAML/JSON) CRUD   ★ NEW ★
#   • api/routers/do_api.py        – Do (Celery enqueue)
#   • api/routers/check_api.py     – Check
#   • api/routers/act_api.py       – Act
#
# 追加・変更ポリシ:
#   1) **破壊的変更は禁止**（追加のみ可）
#   2) /health は include_in_schema=False でドキュメント非公開
# ---------------------------------------------------------------------
from __future__ import annotations

import logging

from fastapi import APIRouter, FastAPI

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# ビルトイン ルータ (存在必須)
# ------------------------------------------------------------------
from api.routers.plan_api import router as plan_router
from api.routers.plan_dsl_api import router as plan_dsl_router   # ★ 追加 ★
from api.routers.do_api import router as do_router

# ------------------------------------------------------------------
# オプション ルータ (未実装ならスタブ登録)
# ------------------------------------------------------------------
# ----- check_router -------------------------------------------------
try:
    from api.routers.check_api import router as check_router  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    logger.warning("[main_api] check_api 未実装 – スタブを登録します")
    check_router = APIRouter(prefix="/check", tags=["check"])

    @check_router.get("/", include_in_schema=True, status_code=501)
    def _check_stub() -> dict[str, str]:
        return {"detail": "Check phase not implemented yet"}

# ----- act_router ---------------------------------------------------
try:
    from api.routers.act_api import router as act_router  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    logger.warning("[main_api] act_api 未実装 – スタブを登録します")
    act_router = APIRouter(prefix="/act", tags=["act"])

    @act_router.get("/", include_in_schema=True, status_code=501)
    def _act_stub() -> dict[str, str]:
        return {"detail": "Act phase not implemented yet"}

# ------------------------------------------------------------------
# FastAPI アプリ本体
# ------------------------------------------------------------------
app = FastAPI(
    title="mmopdca MVP",
    version="0.1.0",
    description="Command-DSL-driven forecasting micro-service (Plan / Do)",
    contact={"name": "gtocue", "email": "gtocue510@gmail.com"},
)

# ------------------------------------------------------------------
# Meta / Utility ルート
# ------------------------------------------------------------------
meta_router = APIRouter(tags=["meta"])


@meta_router.get("/health", include_in_schema=False)
def health() -> dict[str, str]:
    """
    Liveness / Readiness Probe  
    Docker `HEALTHCHECK`, k8s Probe 等から利用。
    """
    return {"status": "ok"}


app.include_router(meta_router)

# ------------------------------------------------------------------
# Business ルート
# ------------------------------------------------------------------
app.include_router(plan_router)
app.include_router(plan_dsl_router)   # ★ DSL ルータを追加 ★
app.include_router(do_router)
app.include_router(check_router)
app.include_router(act_router)

# ------------------------------------------------------------------
# NOTE
# ----
# • 認証ミドルウェアや CORS 設定は api/__init__.py など
#   別ユニットで付与する方針。
# • エラー共通ハンドラも同様に分離して実装する。
# ------------------------------------------------------------------
