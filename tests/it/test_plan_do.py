# =========================================================
# tests/it/test_plan_do.py
# ---------------------------------------------------------
# 外形テスト:
#   ① /plan  で Plan を登録
#   ② /do    をキックして do_id を取得（201）
#   ③ /do/{id} をポーリングして DONE になるのを待つ
# ---------------------------------------------------------
from __future__ import annotations

import asyncio
import uuid

import httpx

# tests/conftest.py で Uvicorn を 8001 ポートに起動済み
BASE = "http://127.0.0.1:8001"


async def _wait_done(do_id: str, timeout: int = 30) -> bool:
    """/do/{id} が DONE|FAILED になるまで最長 `timeout` 秒待機"""
    async with httpx.AsyncClient() as c:
        for _ in range(timeout):
            status = (await c.get(f"{BASE}/do/{do_id}")).json()["status"]
            if status in {"DONE", "FAILED"}:
                return True
            await asyncio.sleep(1)
    return False


def test_plan_do_flow() -> None:
    """Plan 登録 → Do 実行 → DONE までの E2E フロー"""

    # ---------- ① Plan 登録 ----------
    plan_id = f"plan-{uuid.uuid4().hex[:8]}"
    plan = {
        "id":         plan_id,
        "symbol":     "AAPL",
        "start":      "2024-01-01",
        "end":        "2024-12-31",
        "indicators": [{"name": "SMA", "window": 5}],
    }

    with httpx.Client() as c:
        assert c.post(f"{BASE}/plan/", json=plan).status_code == 201

        # ---------- ② Do 実行 ----------
        do_resp = c.post(f"{BASE}/do/{plan_id}")
        assert do_resp.status_code == 201
        do_id = do_resp.json()["do_id"]

    # ---------- ③ 完了待ち ----------
    assert asyncio.run(_wait_done(do_id)), "Do job did not finish in time"
