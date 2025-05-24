"""Shared pytest fixtures for the whole test‑suite.

This file is self‑contained – *no* external stubs or monkey‑patch helpers are
required.  Everything that used to rely on Celery/Redis is replaced by a cheap
in‑process stand‑in so the suite can run on any CI runner without extra
services.
"""
from __future__ import annotations

import importlib
import socket
import threading
import time
from contextlib import closing
from datetime import datetime, timezone
from typing import Any, Iterator

import pytest
import uvicorn
from fastapi import FastAPI

# ────────────────────────────────────────────────────────────────────────────────
# 0.  tiny benchmark fixture (pytest‑benchmark replacement)                     ─
# ────────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def benchmark():  # noqa: D401 – fixture, not function docstring
    """A *very* small shim so the test‑suite can call ``benchmark(fn, *args)``.

    It just runs the function once and returns the value – nothing more.  If
    pytest‑benchmark is installed the real fixture will silently override this
    one, so you still get proper statistics in richer environments.
    """

    def _run(fn: Any, *args: Any, **kwargs: Any):  # noqa: ANN401
        return fn(*args, **kwargs)

    return _run


# ────────────────────────────────────────────────────────────────────────────────
# 1.  Patch *do* and *check* flows so they are synchronous & in‑process          ─
# ────────────────────────────────────────────────────────────────────────────────

# (re)load the module after the test runner has had a chance to monkey‑patch
# anything it likes – that guarantees we have the final symbols.
import api.routers.do_api as _do_api  # noqa: E402  (import after top‑level)
from core.celery_app import celery_app  # noqa: E402
from core.repository.factory import get_repo  # noqa: E402

_do_api = importlib.reload(_do_api)  # type: ignore[assignment]  # refresh


def _dummy_run_do_task(do_id: str, plan_id: str, params: dict):  # noqa: D401
    """Very small replacement for the real Celery task.

    - Marks the *do* record as **DONE** with a perfect score.
    - Runs entirely in‑process / synchronous so the tests don’t need Celery or
      Redis.
    """

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


# Celery’s ``apply_async`` → call synchronously

def _sync_apply_async(*args: Any, **kwargs: Any):  # noqa: ANN401
    _args = kwargs.get("args") or (args[0] if args else ())
    _kwargs = kwargs.get("kwargs", {})
    _dummy_run_do_task(*_args, **_kwargs)


_do_api.run_do_task.apply_async = _sync_apply_async  # type: ignore[attr-defined]


# The *check* phase normally spawns another Celery task – we replace the broker
# call entirely so it writes the finished record immediately.

def _dummy_send_task(name: str, args: list | tuple | None = None, **_: object):
    if not args:
        return

    check_id, do_id = args
    print("dummy_send_task", name, args)

    def _update() -> None:
        repo = get_repo("check")
        now = datetime.now(timezone.utc).isoformat()
        rec = repo.get(check_id) or {}
        rec.update(
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
            }
        )
        repo.upsert(check_id, rec)

    # 2024-06-09: Use a background thread to update the record slightly later
    # instead of ``threading.Timer`` which occasionally fails to fire in CI.
    def _run() -> None:
        time.sleep(0.01)
        _update()

    threading.Thread(target=_run, daemon=True).start()


celery_app.send_task = _dummy_send_task  # type: ignore[assignment]

# ────────────────────────────────────────────────────────────────────────────────
# 2.  Import the FastAPI application *after* monkey‑patching is complete        ─
# ────────────────────────────────────────────────────────────────────────────────
from api.main_api import app  # noqa: E402 – import order is deliberate

assert isinstance(app, FastAPI)  # quick sanity‑check

# ────────────────────────────────────────────────────────────────────────────────
# 3.  A session‑scoped fixture that starts Uvicorn once for the whole run        ─
# ────────────────────────────────────────────────────────────────────────────────

_HOST = "127.0.0.1"
_PORT = 8001


def _port_is_open() -> bool:
    """Return True if something is LISTENing on ``_HOST:_PORT``."""

    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.settimeout(0.2)
        return sock.connect_ex((_HOST, _PORT)) == 0


@pytest.fixture(scope="session", autouse=True)
def serve_api() -> Iterator[None]:
    """Spin up Uvicorn in a background thread for the duration of the test run."""

    if not _port_is_open():
        config = uvicorn.Config(app, host=_HOST, port=_PORT, log_level="warning")
        server = uvicorn.Server(config)
        thread = threading.Thread(target=server.run, daemon=True)
        thread.start()

        # ─ wait (max 5 s) until the port responds ─
        for _ in range(50):
            if _port_is_open():
                break
            time.sleep(0.1)
        else:
            raise RuntimeError(f"Uvicorn failed to start on {_HOST}:{_PORT}")

    yield  # tests run here – nothing else to do
    # The server thread is *daemon*‑ised; Python will stop it automatically.
