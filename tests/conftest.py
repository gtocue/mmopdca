# ─── tests/conftest.py  (インテグレーション共通) ───
from __future__ import annotations

import importlib
import os
import socket
import threading
import time
from contextlib import closing
from typing import Iterator

import pytest
import uvicorn

# ------------------------------------------------------------------ Celery Stub
import api.routers.do_api as _do_api

_do_api = importlib.reload(_do_api)             # 最新ソースで上書き

# Celery タスク kick は NO-OP
_do_api.run_do_task.apply_async = lambda *a, **k: None  # type: ignore[attr-defined]

class _DummyResult:                              # ← AsyncResult の代替
    def __init__(self, task_id: str):
        self.id = task_id
        self._state = "SUCCESS"                  # すぐ SUCCESS

    @property
    def state(self) -> str:
        return self._state

_do_api.AsyncResult = _DummyResult               # type: ignore[attr-defined]

# ------------------------------------------------------------------ FastAPI 起動
from api.main_api import app  # noqa: E402 (reload 後に import)

_HOST, _PORT = "127.0.0.1", 8001                 # ★ ポートは 8001 に統一
os.environ.setdefault("API_BASE_URL", f"http://{_HOST}:{_PORT}")

def _port_open() -> bool:
    with closing(socket.socket()) as s:
        s.settimeout(0.2)
        return s.connect_ex((_HOST, _PORT)) == 0

@pytest.fixture(scope="session", autouse=True)
def _serve_api() -> Iterator[None]:
    if not _port_open():
        srv = uvicorn.Server(uvicorn.Config(app, host=_HOST, port=_PORT, log_level="warning"))
        threading.Thread(target=srv.run, daemon=True).start()
        for _ in range(50):
            if _port_open():
                break
            time.sleep(0.1)
        else:
            raise RuntimeError("Uvicorn failed to start")
    yield
