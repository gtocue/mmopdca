# conftest.py
import os
import time
import threading
import socket
import pytest
import uvicorn
from api.main_api import app

HOST, PORT = "127.0.0.1", 8001

def _port_open() -> bool:
    s = socket.socket()
    s.settimeout(0.2)
    try:
        return s.connect_ex((HOST, PORT)) == 0
    finally:
        s.close()

@pytest.fixture(scope="session", autouse=True)
def serve_app():
    # HTTP & WS をまとめて起動
    if not _port_open():
        server = uvicorn.Server(
            uvicorn.Config(app, host=HOST, port=PORT, log_level="warning")
        )
        thread = threading.Thread(target=server.run, daemon=True)
        thread.start()

        # 起動待ち (最大 5 秒)
        for _ in range(50):
            if _port_open():
                break
            time.sleep(0.1)
        else:
            raise RuntimeError("Uvicorn failed to start")
    yield
