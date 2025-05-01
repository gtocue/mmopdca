# =========================================================
# ASSIST_KEY: 【tests/api/test_do_api.py】
# =========================================================
#
# /do API の簡単 E2E
# ---------------------------------------------------------
import time

def test_do_flow(client):
    # Plan をまず登録
    plan_yaml = (
        "plan_id: sample-001\n"
        "owner: alice@example.com\n"
        "data:\n  source: yfinance\n  universe: [AAPL]\n  frequency: 1d\n"
        "dates:\n  train_start: 2023-01-01\n  train_end: 2024-01-01\n"
        "indicators: {}\n"
    )
    res = client.post("/plan-dsl/", content=plan_yaml.encode(), headers={"Content-Type": "application/x-yaml"})
    assert res.status_code == 201
    plan_id = res.json()["id"]

    # Do キュー投入
    res = client.post(f"/do/{plan_id}")
    assert res.status_code == 202
    task_id = res.json()["task_id"]

    # （同期 Celery 実行環境なら）直後に結果取得
    time.sleep(0.1)
    status = client.get(f"/do/status/{task_id}").json()
    assert status["state"] in {"SUCCESS", "PENDING", "STARTED"}
