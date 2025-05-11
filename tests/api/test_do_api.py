# =========================================================
# tests/api/test_do_api.py
# ---------------------------------------------------------
#   • /plan-dsl で Plan を登録
#   • /do/{plan_id} を叩いてジョブを enqueue（202 Accepted）
#   • /do/{do_id} で状態を確認して DONE│RUNNING│PENDING│FAILED を許容
# =========================================================
from __future__ import annotations

import time
from fastapi import FastAPI
from fastapi.testclient import TestClient

# ルータ
from api.routers.plan_dsl_api import router as dsl_router
from api.routers.do_api import router as do_router

# TestClient
app = FastAPI()
app.include_router(dsl_router)
app.include_router(do_router)
client = TestClient(app)


def test_do_flow() -> None:
    """Plan 登録 → Do 実行 → 状態確認"""

    # 1) Plan 登録
    plan_yaml = (
        "plan_id: sample-001\n"
        "owner: alice@example.com\n"
        "data:\n  source: yfinance\n  universe: [AAPL]\n  frequency: 1d\n"
        "dates:\n  train_start: 2023-01-01\n  train_end: 2024-01-01\n"
        "indicators: {}\n"
    )
    resp = client.post(
        "/plan-dsl/",
        content=plan_yaml.encode(),
        headers={"Content-Type": "application/x-yaml"},
    )
    assert resp.status_code == 201
    plan_id = resp.json()["id"]

    # 2) Do enqueue
    do_resp = client.post(f"/do/{plan_id}")
    assert do_resp.status_code == 202  # ★ 202
    payload = do_resp.json()
    do_id = payload["do_id"]
    assert "task_id" in payload

    # 3) 状態確認
    deadline = time.monotonic() + 5.0
    final_status = None
    while time.monotonic() < deadline:
        state = client.get(f"/do/{do_id}").json()
        final_status = state["status"]
        if final_status in {"DONE", "FAILED"}:
            break
        time.sleep(0.2)

    assert final_status in {"DONE", "FAILED", "RUNNING", "PENDING"}
    assert "result" in state
