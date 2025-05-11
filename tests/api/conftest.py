# tests/api/conftest.py
from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

# ルータ
from api.routers.plan_dsl_api import router as dsl_router
import api.routers.plan_dsl_api as plan_dsl_module
import api.routers.do_api as do_module  # ← 追加

# MemoryRepo で本番 DB 依存を切る
from core.repository.memory_impl import MemoryRepository


@pytest.fixture(autouse=True)
def _patch_repo(monkeypatch: pytest.MonkeyPatch):
    """
    plan_dsl も do_api も **同じ** MemoryRepository インスタンスを共有する。
    """
    mem_plan_repo = MemoryRepository(table="plan")
    mem_do_repo = MemoryRepository(table="do")

    # Plan DSL ルータ
    monkeypatch.setattr(plan_dsl_module, "_repo", mem_plan_repo, raising=True)

    # Do ルータ
    monkeypatch.setattr(do_module, "_plan_repo", mem_plan_repo, raising=True)
    monkeypatch.setattr(do_module, "_do_repo", mem_do_repo, raising=True)


@pytest.fixture()
def client() -> TestClient:
    app = FastAPI()
    app.include_router(dsl_router)
    # do_router はテストスコープで import された時点で repo が差し替わっている
    app.include_router(do_module.router)
    return TestClient(app)
