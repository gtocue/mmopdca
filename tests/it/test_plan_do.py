# tests/it/test_plan_do.py
import uuid, httpx, asyncio

BASE = "http://127.0.0.1:8000"

async def wait_done(do_id: str, timeout=15):
    async with httpx.AsyncClient() as c:
        for _ in range(timeout):
            r = await c.get(f"{BASE}/do/{do_id}")
            if r.json()["status"] == "DONE":
                return True
            await asyncio.sleep(1)
    return False

def test_plan_do_flow():
    plan_id = f"plan-{uuid.uuid4().hex[:8]}"
    plan = {
        "id": plan_id,
        "symbol": "AAPL",
        "start": "2024-01-01",
        "end":   "2024-12-31",
        "indicators": [{"name":"SMA","window":5}],
    }
    with httpx.Client() as c:
        assert c.post(f"{BASE}/plan/", json=plan).status_code == 201
        do_r = c.post(f"{BASE}/do/{plan_id}", json={"symbol":"AAPL","start":"2024-01-01","end":"2024-12-31"})
        do_id = do_r.json()["do_id"]
    assert asyncio.run(wait_done(do_id))
