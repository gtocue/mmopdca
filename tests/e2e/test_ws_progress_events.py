# test_ws_progress_events.py
import os
from starlette.testclient import TestClient
from api.main_api import app

client = TestClient(app)
BASE = "/ws"

def test_ws_progress_events():
    run_id = "test-run-id"
    headers = {"x-api-key": os.getenv("API_KEY")} if os.getenv("API_KEY") else {}
    with client.websocket_connect(f"{BASE}/{run_id}", headers=headers) as ws:
        for i in range(1, 6):
            data = ws.receive_json()
            assert data.get("progress") == i
