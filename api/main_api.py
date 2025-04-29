# ====================================================================== 
# ASSIST_KEY: 【api/main_api.py】  ─ FastAPI エントリポイント (MVP)
# ======================================================================
# 【概要】
#   mmopdca “MVP ルータ集約サービス”。各サブ API を 1 つの FastAPI
#   インスタンスにマウントし、Swagger UI（/docs）を公開。
#
# 【主な役割】
#   - plan / do / check / act の 4 ルータを include
#   - /health  エンドポイントでコンテナの L4/L7 ヘルスチェックに対応
#
# 【連携先・依存関係】
#   - api/routers/plan_api.py   (計画フェーズ CRUD)
#   - api/routers/do_api.py     (実行フェーズ: Celery タスク投げ)
#   - api/routers/check_api.py  (検証フェーズ)
#   - api/routers/act_api.py    (改善フェーズ)
#
# 【ルール遵守】
#   1) 追加機能のみ（breaking change は要相談）
#   2) PDCA 各フェーズは独立 Router として分割・疎結合
#   3) 型安全・ハルシネーション禁止
#
# 【備考】
#   - include_in_schema=False で /health は Swagger UI に出さない。
#   - 将来的にバージョンネゴシエーションが必要になれば
#     /v1/plan … のように prefix を付ける。
# ----------------------------------------------------------------------

from __future__ import annotations

from fastapi import APIRouter, FastAPI

from api.routers.act_api import router as act_router
from api.routers.check_api import router as check_router
from api.routers.do_api import router as do_router
from api.routers.plan_api import router as plan_router

# ---------------------------------------------------------------------
# FastAPI アプリ本体
# ---------------------------------------------------------------------
app = FastAPI(
    title="mmopdca MVP",
    version="0.1.0",
    description="Command-DSL-driven forecasting micro-service",
)

# ---------------------------------------------------------------------
# Meta / ユーティリティルート
# ---------------------------------------------------------------------
meta_router = APIRouter(tags=["Meta"])


@meta_router.get("/health", include_in_schema=False)
def health() -> dict[str, str]:
    """
    Liveness / Readiness Probe 用の軽量エンドポイント  
    - Docker `HEALTHCHECK`, LB, k8s Probe で活用
    """
    return {"status": "ok"}


app.include_router(meta_router)

# ---------------------------------------------------------------------
# ビジネスルータ
# ---------------------------------------------------------------------
app.include_router(plan_router)
app.include_router(do_router)
app.include_router(check_router)
app.include_router(act_router)

# NOTE:
# - 認証ミドルウェアや CORS 設定は別ユニットで行う想定
# - エラー共通ハンドラは api/routers/__init__.py 側で登録する計画
