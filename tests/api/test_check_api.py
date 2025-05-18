# tests/api/test_check_api.py

import time
import uuid

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

# 既存の fixtures がマウントするルータ
from api.routers.plan_dsl_api import router as plan_router
from api.routers.do_api import router as do_router
# 追加: チェック用ルータ
from api.routers.check_api import router as check_router


@pytest.fixture()
def client_for_check(monkeypatch) -> TestClient:
    """
    plan_dsl_api, do_api, check_api の３つを同時にマウントした TestClient.
    conftest.py 側で MemoryRepository をモンキーパッチしている前提です。
    """
    app = FastAPI()
    app.include_router(plan_router)
    app.include_router(do_router)
    app.include_router(check_router)
    return TestClient(app)


def test_check_flow(client_for_check: TestClient):
    # ---- 1) Plan 登録 ----
    plan_id = f"test-plan-{uuid.uuid4().hex[:6]}"
    yaml_payload = (
        "plan_id: " + plan_id + "\n"
        "owner: bob@example.com\n"
        "data:\n"
        "  source: yfinance\n"
        "  universe: [GOOG]\n"
        "  frequency: 1d\n"
        "dates:\n"
        "  train_start: 2023-01-01\n"
        "  train_end:   2024-01-01\n"
        "indicators: {}\n"
    )
    res_plan = client_for_check.post(
        "/plan-dsl/",
        content=yaml_payload.encode(),
        headers={"Content-Type": "application/x-yaml"},
    )
    assert res_plan.status_code == 201
    # ---- 2) Do キック ----
    do_resp = client_for_check.post(f"/do/{plan_id}")
    assert do_resp.status_code == 202
    do_id = do_resp.json()["do_id"]

    # ---- 3) Do 完了待ち ----
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        state = client_for_check.get(f"/do/{do_id}").json().get("status")
        if state in ("DONE", "FAILED"):
            break
        time.sleep(0.2)
    assert state in ("DONE", "FAILED")

    # ---- 4) Check キック ----
    chk_resp = client_for_check.post(f"/check/{do_id}", json={})
    assert chk_resp.status_code == 202
    check_id = chk_resp.json()["id"]

    # ---- 5) Check 完了待ち & レポート検証 ----
    deadline = time.monotonic() + 5
    report = None
    while time.monotonic() < deadline:
        rep = client_for_check.get(f"/check/{check_id}").json()
        if rep.get("report") is not None:
            report = rep["report"]
            break
        time.sleep(0.2)

    assert report is not None, "report が生成されなかった"
    # 例: ステータスキーが SUCCESS or FAILURE になっているはず
    assert report["status"] in ("SUCCESS", "FAILURE")
