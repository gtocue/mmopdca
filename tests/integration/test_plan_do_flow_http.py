# tests/integration/test_plan_do_flow_http.py
import os
import time
import requests
import pytest

BASE = os.getenv("API_BASE_URL", "http://127.0.0.1:8001")


def _wait_for_health(base_url: str, timeout: int = 10) -> bool:
    """Return ``True`` if ``GET /health`` succeeds within ``timeout`` seconds."""

    deadline = time.time() + timeout
    health_url = f"{base_url.rstrip('/')}/health"
    while time.time() < deadline:
        try:
            if requests.get(health_url, timeout=3).status_code == 200:
                return True
        except requests.RequestException:
            pass
        time.sleep(1)
    return False

@pytest.mark.integration
def test_plan_do_flow_http():
    if not _wait_for_health(BASE):
        pytest.skip("API server not reachable")
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
