# =========================================================
# tests/api/conftest.py
# ---------------------------------------------------------
# FastAPI ルータ単体をメモリリポジトリでテストするための
# TestClient を提供（外部 DB / Celery 完全排除）。
# =========================================================
from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

# 対象ルータ ------------------------------------------------
from api.routers.plan_dsl_api import router as dsl_router
import api.routers.plan_dsl_api as plan_dsl_module

# メモリリポジトリ実装 --------------------------------------
from core.repository.memory_impl import MemoryRepository


# ----------------------------------------------------------------------
# fixture: ルータ内の `_repo` を MemoryRepository へ差し替え
# ----------------------------------------------------------------------
@pytest.fixture(autouse=True)
def _patch_repo(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    plan_dsl_api が参照する _repo をメモリ版に置換する。

    * raising=True で「属性名が存在しない」場合は即テスト失敗
    * 他テストへの副作用を避けるため、毎テスト後に自動でリセット
    """
    monkeypatch.setattr(
        plan_dsl_module,
        "_repo",
        MemoryRepository(table="plan"),
        raising=True,
    )


# ----------------------------------------------------------------------
# fixture: TestClient
# ----------------------------------------------------------------------
@pytest.fixture()
def client() -> TestClient:
    """plan_dsl ルータのみをマウントした極小 FastAPI アプリ。"""
    app = FastAPI()
    app.include_router(dsl_router)
    return TestClient(app)
