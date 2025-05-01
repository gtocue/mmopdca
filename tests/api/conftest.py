# =========================================================
# ASSIST_KEY: 【tests/api/conftest.py】
# =========================================================
#
# 【概要】
#   FastAPI ルータと MemoryRepository で API テスト用の
#   TestClient を提供。
# ---------------------------------------------------------

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

# ルータ
from api.routers.plan_dsl_api import router as dsl_router

# MemoryRepo で本番 DB 依存を切る
from core.repository.memory_impl import MemoryRepository
import api.routers.plan_dsl_api as plan_dsl_module


@pytest.fixture(autouse=True)
def _patch_repo(monkeypatch: pytest.MonkeyPatch):
    """API ルータ内の _repo をメモリ実装に差し替え."""
    monkeypatch.setattr(
        plan_dsl_module, "_repo", MemoryRepository(table="plan"), raising=True
    )


@pytest.fixture()
def client() -> TestClient:
    app = FastAPI()
    app.include_router(dsl_router)
    return TestClient(app)
