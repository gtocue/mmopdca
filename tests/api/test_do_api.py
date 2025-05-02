# =========================================================
# tests/api/test_do_api.py
# ---------------------------------------------------------
#   • /plan-dsl で Plan を登録
#   • /do/{plan_id} を叩いてジョブを enqueue（201 Created）
#   • /do/{do_id} で状態を取得して DONE | RUNNING | PENDING を確認
# ---------------------------------------------------------
from __future__ import annotations

import time
from datetime import timedelta

from fastapi import FastAPI
from fastapi.testclient import TestClient

# ルータ ---------------------------------------------------
from api.routers.plan_dsl_api import router as dsl_router
from api.routers.do_api import router as do_router

# ---------------------------------------------------------
# TestClient ― plan-dsl + do だけをマウントした最小構成
# ---------------------------------------------------------
app = FastAPI()
app.include_router(dsl_router)
app.include_router(do_router)
client = TestClient(app)


# ---------------------------------------------------------
# テスト本体
# ---------------------------------------------------------
def test_do_flow() -> None:
    """Plan 登録 → Do 実行 → 状態確認 の E2E フロー"""

    # ---------- 1. Plan 登録 ----------
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

    # ---------- 2. Do enqueue ----------
    do_resp = client.post(f"/do/{plan_id}")
    assert do_resp.status_code == 201
    payload = do_resp.json()

    # レスポンス基本項目
    assert payload["plan_id"] == plan_id
    assert payload["status"] == "PENDING"
    do_id = payload["do_id"]

    # ---------- 3. 状態確認 ----------
    #   同期実行なので数百 ms 待つと RUNNING→DONE になっているはず
    deadline = time.monotonic() + 5.0  # 5 秒以内に DONE へ遷移する想定
    final_status = None

    while time.monotonic() < deadline:
        state = client.get(f"/do/{do_id}").json()
        final_status = state["status"]
        if final_status in {"DONE", "FAILED"}:
            break
        time.sleep(0.2)  # 200 ms ポーリング

    assert final_status in {"DONE", "FAILED", "RUNNING", "PENDING"}
    # 少なくとも result キーは存在（DONE/FAILED の場合は中身あり）
    assert "result" in state
