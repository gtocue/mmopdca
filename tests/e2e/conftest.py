import socket
import threading
import time

import pytest
import uvicorn
from api.main_api import app as _app

HOST, PORT = "127.0.0.1", 8001


def _port_open() -> bool:
    """Return True if the application port is open."""
    sock = socket.socket()
    sock.settimeout(0.2)
    return sock.connect_ex((HOST, PORT)) == 0


@pytest.fixture(scope="session", autouse=True)
def serve_app() -> None:
    """Start the API for the duration of the test session."""
    if not _port_open():
        server = uvicorn.Server(
            uvicorn.Config(_app, host=HOST, port=PORT, log_level="warning")
        )
        thread = threading.Thread(target=server.run, daemon=True)
        thread.start()

        for _ in range(50):
            if _port_open():
                break
            time.sleep(0.1)
        else:
            raise RuntimeError("Uvicorn failed to start")

    yield