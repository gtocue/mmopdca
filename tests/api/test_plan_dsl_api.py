"""tests/api/test_plan_dsl_api.py — E2E + Unit tests

• E2E : /plan-dsl/  POST (multipart) → GET
• Unit: baseline セクションが DSLValidator を通過することを検証
"""
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from fastapi.testclient import TestClient

# ----- FastAPI app import ---------------------------------------------------
# app 本体が api/main_api.py にある前提
from api.main_api import app

# ----- validator import -----------------------------------------------------
from core.dsl.validator import DSLValidator  # noqa: E402

if TYPE_CHECKING:  # for type checkers / Pylance
    from fastapi import FastAPI

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def client() -> TestClient:
    """Reusable FastAPI test client."""
    return TestClient(app)  # type: ignore[arg-type]


@pytest.fixture(scope="module")
def validator() -> DSLValidator:
    """DSLValidator instance pointing to local schema directory."""
    schemas_dir = Path(__file__).parents[2] / "core" / "dsl" / "schemas"
    return DSLValidator(schemas_dir=schemas_dir)


# ---------------------------------------------------------------------------
# E2E test
# ---------------------------------------------------------------------------

SAMPLE_BYTES = Path("samples/plan_mvp.yaml").read_bytes()


def test_create_and_get_plan(client: TestClient) -> None:
    """Create → Get round-trip for /plan-dsl/ endpoint."""
    res = client.post(
        "/plan-dsl/",
        files={"file": ("plan_mvp.yaml", SAMPLE_BYTES, "application/x-yaml")},
    )
    assert res.status_code == 201
    body = res.json()
    plan_id = body["id"]
    assert body["data"]["universe"] == ["MSFT"]

    res2 = client.get(f"/plan-dsl/{plan_id}")
    assert res2.status_code == 200
    assert res2.json()["id"] == plan_id


# ---------------------------------------------------------------------------
# Unit test – baseline validation
# ---------------------------------------------------------------------------


def test_plan_with_valid_baseline(validator: DSLValidator) -> None:
    """Baseline params should pass pydantic validation (no exception)."""
    plan = {
        "timestamp": "date",
        "target": "sales",
        "baseline": {"lookback_days": 30, "strategy": "mean"},
    }
    validator.validate_plan(plan)  # should not raise
