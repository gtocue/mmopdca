import time
import threading
import socket
import pytest
import uvicorn
from api.main_api import app as _app

HOST, PORT = "127.0.0.1", 8001
def _port_open():

    s = socket.socket()
 s.settimeout(0.2)
    return s.connect_ex((HOST, PORT)) == 0

@pytest.fixture(scope="session", autouse=True)
def serve_app():

    # WS および HTTP API 両方を立ち上げ
    if not _port_open():

        server = uvicorn.Server(uvicorn.Config(_app, host=HOST, port=PORT, log_level="warning"))
        thread = threading.Thread(target=server.run, daemon=True)
        thread.start()
        for _ in range(50):

            if _port_open(): break
            time.sleep(0.1)
        else:

            raise RuntimeError("Uvicorn failed to start")
    yield
