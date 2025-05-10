import time, requests, pytest

API = "http://127.0.0.1:8000"

def test_plan_do_check():
    plan = requests.post(f"{API}/plan/",
                         json={"symbol":"AAPL",
                               "start":"2024-01-01",
                               "end":"2024-12-31"}).json()

    do   = requests.post(f"{API}/do/{plan['id']}", json={}).json()

    # --- wait Do ---
    for _ in range(120):
        rec = requests.get(f"{API}/do/{do['do_id']}").json()
        if rec["status"] == "DONE":
            break
        time.sleep(1)
    else:
        pytest.fail("Do did not finish")

    check = requests.post(f"{API}/check/{do['do_id']}").json()

    # --- wait Check ---
    for _ in range(120):
        rep = requests.get(f"{API}/check/{check['id']}").json()
        if rep.get("report"):
            assert rep["report"]["status"] == "SUCCESS"
            return
        time.sleep(2)
    pytest.fail("Check did not finish")
