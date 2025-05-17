# tests/e2e_ws.py

import os
import json
import pytest
from starlette.testclient import TestClient
from api.main_api import app

# WebSocket のベースパス
BASE_WS_PATH = "/ws"

# FastAPI アプリを TestClient でラップ
client = TestClient(app)


def test_ws_progress_events():
    """
    /ws/{run_id} に接続して、
    progress イベントを 5 回受信できることを同期的に確認します。
    """

    run_id = "test-run-id"

    # PowerShell なら以下のように設定してください
    # PS> $Env:API_KEY="dummy-key"
    api_key = os.getenv("API_KEY")
    headers = {"x-api-key": api_key} if api_key else {}

    # コンテキストマネージャを抜けると自動で close されます
    with client.websocket_connect(f"{BASE_WS_PATH}/{run_id}", headers=headers) as ws:
        for expected in range(1, 6):
            data = ws.receive_json()
            assert "progress" in data, f"no progress in {data}"
            assert (
                data["progress"] == expected
            ), f"expected {expected}, got {data['progress']}"

    # 到達すれば OK
