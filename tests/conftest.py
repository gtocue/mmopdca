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
# pytest-benchmark が無い環境向けの簡易ベンチマーク fixture
# ----------------------------------------------------------------------

@pytest.fixture
def benchmark():
    """Minimal benchmark fixture compatible with pytest-benchmark."""

    def run(fn, *args, **kwargs):
        return fn(*args, **kwargs)

    return run

# ----------------------------------------------------------------------
# ① do_api を “同期・HTTP 202 版” に確実に差し替え
# ----------------------------------------------------------------------
import api.routers.do_api as _do_api
from datetime import datetime, timezone
from core.repository.factory import get_repo
from core.celery_app import celery_app

# キャッシュを消して最新ソースをロード
_do_api = importlib.reload(_do_api)  # noqa: PLW0603

# Celery を使わないため run_do_task 自体をスタブ実装に差し替える
def _dummy_run_do_task(do_id: str, plan_id: str, params: dict) -> None:
    """Simplified run_do_task used for unit tests."""
    repo = get_repo("do")
    now = datetime.now(timezone.utc).isoformat()
    repo.upsert(
        do_id,
        {
            "do_id": do_id,
            "plan_id": plan_id,
            "status": "DONE",
            "result": {
                "r2": 1.0,
                "rmse": 0.0,
                "threshold": 0.8,
                "passed": True,
            },
            "completed_at": now,
        },
    )


def _sync_apply_async(*args, **kwargs):
    _args = kwargs.get("args") or (args[0] if args else ())
    _kwargs = kwargs.get("kwargs", {})
    _dummy_run_do_task(*_args, **_kwargs)


_do_api.run_do_task.apply_async = _sync_apply_async  # type: ignore[attr-defined]


# Check フェーズも Celery を使わずに即時実行するスタブ
def _dummy_send_task(name: str, args: list | tuple | None = None, **_: object) -> None:
    if not args:
        return
    check_id, do_id = args
    repo = get_repo("check")
    now = datetime.now(timezone.utc).isoformat()
    repo.upsert(
        check_id,
        {
            "id": check_id,
            "do_id": do_id,
            "status": "SUCCESS",
            "report": {
                "status": "SUCCESS",
                "r2": 1.0,
                "threshold": 0.8,
                "passed": True,
            },
            "completed_at": now,
        },
    )


celery_app.send_task = _dummy_send_task  # type: ignore[assignment]

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
