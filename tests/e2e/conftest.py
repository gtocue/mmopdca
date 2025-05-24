# tests/e2e/conftest.py
"""
E2E テスト共通 ﬁxture:
pytest セッション開始時に Uvicorn をバックグラウンド起動し、
すでに LISTEN 済みなら再利用する。
"""

from __future__ import annotations

import socket
import threading
import time
from contextlib import closing
from typing import Iterator

import pytest
import uvicorn
from api.main_api import app as _app  # isort: skip

_HOST = "127.0.0.1"
_PORT = 8001


def _port_is_open(host: str = _HOST, port: int = _PORT, timeout: float = 0.2) -> bool:
    """Return True if the TCP port is already LISTENing."""
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.settimeout(timeout)
        return s.connect_ex((host, port)) == 0


@pytest.fixture(scope="session", autouse=True)
def serve_app() -> Iterator[None]:
    """
    * pytest セッション全体で 1 度だけ Uvicorn を起動  
    * 既に LISTEN 済みならそのまま流用する
    """
    if not _port_is_open():
        cfg = uvicorn.Config(_app, host=_HOST, port=_PORT, log_level="warning")
        server = uvicorn.Server(cfg)
        threading.Thread(target=server.run, daemon=True).start()

        # 最大 5 秒待機
        for _ in range(50):  # 50 × 0.1 s = 5 s
            if _port_is_open():
                break
            time.sleep(0.1)
        else:
            raise RuntimeError(f"Uvicorn failed to start on {_HOST}:{_PORT}")

    yield  # ── テスト実行 ──
    # デーモンスレッドなので pytest 終了時に自動終了
