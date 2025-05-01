# =========================================================
# ASSIST_KEY: このファイルは【gateway/tests/test_router.py】に位置するユニットです
# =========================================================
#
# 【概要】
#   このユニットは /forecast ルータのユニットテスト (pytest) を提供します。
#
# 【主な役割】
#   - FastAPI テストクライアントで 200 / 401 応答を検証
#   - mmop_bridge.run_forecast を monkeypatch し外部 HTTP を呼ばせない
#
# 【連携先・依存関係】
#   - gateway/api/router.py        … 対象ルータ
#   - pytest, httpx[async]         … テストライブラリ
#
# 【ルール遵守】
#   1) 外部サービス呼び出しを行わない（完全スタブ）
#   2) ハードコード値は # FIXME マーク
# ---------------------------------------------------------

from __future__ import annotations

import asyncio
from typing import Any

import pytest
from fastapi import FastAPI
from httpx import AsyncClient

from gateway.api.router import router as forecast_router
from gateway.adapter.mmop_bridge import ForecastRequest, ForecastResponse


@pytest.fixture()
def app() -> FastAPI:
    """Minimal FastAPI app including only forecast router."""
    app_ = FastAPI()
    app_.include_router(forecast_router)
    return app_


@pytest.fixture(autouse=True)
def patch_run_forecast(monkeypatch):
    """Monkey-patch run_forecast to avoid real HTTP calls."""
    async def _dummy_run_forecast(req: ForecastRequest) -> ForecastResponse:  # noqa: D401
        return ForecastResponse(
            forecast=0.012,
            ci_lower=-0.008,
            ci_upper=0.032,
            model_sha="deadbeef",
            hash_link="https://worm/mmopdca/abc123/root.json",
        )

    monkeypatch.setattr(
        "gateway.adapter.mmop_bridge.run_forecast",
        _dummy_run_forecast,
        raising=True,
    )


@pytest.mark.asyncio
async def test_forecast_success(app: FastAPI):
    async with AsyncClient(app=app, base_url="http://test") as ac:
        res = await ac.post(
            "/forecast",
            headers={"X-API-Key": "test-key"},  # key チェックは stub 認証が通る想定
            json={"target": "SPY", "horizon": 5},
        )
    assert res.status_code == 200
    body = res.json()
    assert body["forecast"] == pytest.approx(0.012)


@pytest.mark.asyncio
async def test_forecast_unauthorized(app: FastAPI, monkeypatch):
    """No header → 401"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        res = await ac.post("/forecast", json={"target": "SPY", "horizon": 1})
    assert res.status_code == 401
