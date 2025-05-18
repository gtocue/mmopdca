# test_do_flow_api.py
import os
import time
from pathlib import Path

import pytest
import requests

def _wait_for_health(base_url: str, timeout: int = 30):
    """GET /health が 200 になるまで待機"""
    deadline = time.time() + timeout
    health_url = f"{base_url.rstrip('/')}/health"
    while time.time() < deadline:
        try:
            if requests.get(health_url, timeout=3).status_code == 200:
                return
        except requests.RequestException:
            pass
        time.sleep(2)
    raise RuntimeError("API health-check did not become ready in time")

@pytest.mark.integration
def test_do_flow_api(tmp_path):
    """
    End-to-end smoke-test:
      1. /health の起動確認
      2. Plan 登録
      3. Do キック → タスク完了までポーリング
    """
    base_url = os.getenv("API_BASE_URL", "http://localhost:8001")
    _wait_for_health(base_url)

    # Plan 登録用のユニーク ID
    plan_id = f"pytest-demo-{int(time.time())}"
    sample_yaml = (
        Path(__file__).parents[1] / "samples" / "plan_simple.yaml"
    ).read_text(encoding="utf-8").replace("msft-demo-2024", plan_id)

    # 2) Plan 登録
    resp = requests.post(
        f"{base_url}/plan-dsl/",
        data=sample_yaml,
        headers={"Content-Type": "application/x-yaml"},
        timeout=10,
    )
    assert resp.status_code == 201, resp.text

    # 3) Do キック
    resp = requests.post(f"{base_url}/do/{plan_id}", timeout=10)
    assert resp.status_code == 202, resp.text
    task_id = resp.json()["task_id"]

    # 4) Do タスク完了（SUCCESS/FAILURE）までポーリング
    deadline = time.time() + 120
    status_url = f"{base_url}/do/status/{task_id}"
    while time.time() < deadline:
        state = requests.get(status_url, timeout=10).json()["state"]
        if state in ("SUCCESS", "FAILURE"):
            break
        time.sleep(5)
    else:
        pytest.fail("Do task did not finish within timeout")

    assert state == "SUCCESS", f"run_do finished with {state}"
