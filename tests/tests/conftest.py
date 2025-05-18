from __future__ import annotations

import importlib
import socket
import threading
import time
from contextlib import closing
from typing import Iterator

import pytest
import uvicorn

# ----------------------------------------------------------------------
# ① do_api を “同期・HTTP 202 版” に確実に差し替え
# ----------------------------------------------------------------------
import api.routers.do_api as _do_api

# キャッシュを消して最新ソースをロード
_do_api = importlib.reload(_do_api)  # noqa: PLW0603

# Celery を使わないため apply_async を NO-OP へダミーパッチ
_do_api.run_do_task.apply_async = lambda *_, **__: None  # type: ignore[attr-defined]

# ----------------------------------------------------------------------
# ② FastAPI アプリ本体（※ do_api リロード済み状態で import）
# ----------------------------------------------------------------------
from api.main_api import app  # noqa: E402

# ----------------------------------------------------------------------
# ③ Uvicorn 起動設定
# ----------------------------------------------------------------------
_HOST = "127.0.0.1"
_PORT = 8001

def _port_is_open() -> bool:
    """ポートが LISTEN 中なら True"""
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.settimeout(0.2)
        return sock.connect_ex((_HOST, _PORT)) == 0

@pytest.fixture(scope="session", autouse=True)
def serve_api() -> Iterator[None]:
    """
    pytest セッション全体で Uvicorn をバックグラウンド起動する。
    すでに同ポートで LISTEN していれば再起動せずに流用する。
    """
    if not _port_is_open():
        config = uvicorn.Config(app, host=_HOST, port=_PORT, log_level="warning")
        server = uvicorn.Server(config)
        thread = threading.Thread(target=server.run, daemon=True)
        thread.start()

        # 起動待ち (最大 5 秒)
        for _ in range(50):
            if _port_is_open():
                break
            time.sleep(0.1)
        else:
            raise RuntimeError(f"Uvicorn failed to start on {_HOST}:{_PORT}")

    yield
    # デーモンスレッドなので明示シャットダウン不要
