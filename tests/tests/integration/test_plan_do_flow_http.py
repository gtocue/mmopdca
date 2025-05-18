# tests/integration/test_plan_do_flow_http.py
import time
import requests
import pytest

BASE = "http://127.0.0.1:8001"  # 適宜環境変数化してもよい

@pytest.mark.integration
def test_plan_do_flow_http():
    # 1) Plan 登録
    resp = requests.post(f"{BASE}/plan-dsl/", json={
        "symbol": "AAPL",
        "start": "2024-01-01",
        "end":   "2024-12-31",
    })
    assert resp.status_code == 201
    plan_id = resp.json()["id"]

    # 2) Do 登録
    resp = requests.post(f"{BASE}/do/{plan_id}", json={})
    assert resp.status_code == 202
    do_id = resp.json()["do_id"]

    # 3) 完了待ち（最大60秒）
    for _ in range(60):
        rec = requests.get(f"{BASE}/do/{do_id}").json()
        if rec["status"] == "DONE":
            break
        time.sleep(1)
    else:
        pytest.fail("Do did not finish within timeout")

    # 4) Check 登録＆完了待ち
    resp = requests.post(f"{BASE}/check/{do_id}", json={})
    assert resp.status_code == 202
    check_id = resp.json()["id"]

    for _ in range(60):
        rep = requests.get(f"{BASE}/check/{check_id}").json()
        if rep.get("report"):
            assert rep["report"]["status"] == "SUCCESS"
            return
        time.sleep(1)
    pytest.fail("Check did not finish within timeout")
