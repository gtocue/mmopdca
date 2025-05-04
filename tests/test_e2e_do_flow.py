import os
import time
from pathlib import Path

import pytest
import requests

def _wait_for_health(base_url: str, timeout: int = 30):
    """Block until GET /health returns 200 or timeout (s) expires."""
    deadline = time.time() + timeout
    url = f"{base_url.rstrip('/')}/health"
    while time.time() < deadline:
        try:
            if requests.get(url, timeout=3).status_code == 200:
                return
        except requests.RequestException:
            pass
        time.sleep(2)
    raise RuntimeError("API health‑check did not become ready in time")


@pytest.mark.e2e
def test_do_flow(tmp_path):
    """End‑to‑end smoke‑test: Plan → Do → SUCCESS."""
    base_url = os.getenv("API_BASE_URL", "http://localhost:8001")

    # 1. API up?
    _wait_for_health(base_url)

    # 2. Prepare a unique plan_id so we can run repeatedly without cleanup
    plan_id = f"pytest‑demo‑{int(time.time())}"

    sample_yaml_path = Path(__file__).parents[1] / "samples" / "plan_simple.yaml"
    yaml_txt = sample_yaml_path.read_text(encoding="utf‑8")
    yaml_txt = yaml_txt.replace("msft-demo-2024", plan_id)

    # 3. Register Plan
    resp = requests.post(
        f"{base_url}/plan-dsl/", data=yaml_txt, headers={"Content-Type": "application/x-yaml"}, timeout=10
    )
    assert resp.status_code == 201, resp.text

    # 4. Kick Do
    resp = requests.post(f"{base_url}/do/{plan_id}", timeout=10)
    assert resp.status_code == 202, resp.text
    task_id = resp.json()["task_id"]

    # 5. Poll until SUCCESS/FAILURE
    deadline = time.time() + 120  # 2 min budget (shards are small in sample)
    status_url = f"{base_url}/do/status/{task_id}"
    while time.time() < deadline:
        state = requests.get(status_url, timeout=10).json()["state"]
        if state in ("SUCCESS", "FAILURE"):
            break
        time.sleep(5)
    else:
        pytest.fail("Do task did not finish within timeout")

    assert state == "SUCCESS", f"run_do finished with {state}"
