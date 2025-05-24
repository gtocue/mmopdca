# tests/e2e/conftest.py   ← **完全版**

"""
E2E テスト用の共有 ﬁxture。

* pytest セッション開始時に Uvicorn をバックグラウンド起動
* 既に同ポートで LISTEN していれば再利用
"""

from __future__ import annotations

import socket
import threading
import time
from typing import Iterator

import pytest
import uvicorn

# FastAPI アプリ本体
from api.main_api import app as _app  # isort: skip

_HOST = "127.0.0.1"
_PORT = 8001


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _port_is_open(host: str = _HOST, port: int = _PORT) -> bool:
    """`host:port` が LISTEN 状態かを確認して True/False を返す。"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.2)
        return s.connect_ex((host, port)) == 0


# --------------------------------------------------------------------------- #
# Session-scoped Uvicorn サーバー ﬁxture
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="session", autouse=True)
def serve_app() -> Iterator[None]:
    """
    * セッション開始時に Uvicorn をデーモンスレッドで起動
    * 既に LISTEN 済みならそのまま流用（CI の並列実行対策）
    """

    if not _port_is_open():
        config = uvicorn.Config(_app, host=_HOST, port=_PORT, log_level="warning")
        server = uvicorn.Server(config)

        thread = threading.Thread(target=server.run, daemon=True)
        thread.start()

        # 最大 5 秒だけ起動をポーリング
        for _ in range(50):
            if _port_is_open():
                break
            time.sleep(0.1)
        else:
            raise RuntimeError(f"Uvicorn failed to start on {_HOST}:{_PORT}")

    # ここでテスト実行に制御を戻す
    yield

    # デーモンスレッドなので明示的な shutdown は不要
