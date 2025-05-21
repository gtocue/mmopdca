"""
/health   : GET -> 200/503 + JSON
/healthz  : GET or HEAD -> 204/503 (Kubernetes probe)
"""

from __future__ import annotations

import contextlib
import os
import socket
import time
from typing import Any, Callable, Dict, Tuple

import psycopg2
from fastapi import APIRouter, Request, Response, status
from fastapi.responses import JSONResponse

# ── 接続設定 ─────────────────────────────────────────────
_PG_DSN = dict(
    dbname=os.getenv("POSTGRES_DB", "postgres"),
    user=os.getenv("POSTGRES_USER", "postgres"),
    password=os.getenv("POSTGRES_PASSWORD", ""),
    host=os.getenv("POSTGRES_HOST", "localhost"),
    port=int(os.getenv("POSTGRES_PORT", "5432")),
    connect_timeout=2,
)
_REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
_REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
_REDIS_TIMEOUT = 2  # sec
# ────────────────────────────────────────────────────────


def _check_postgres() -> Tuple[str, bool, float]:
    t0 = time.perf_counter()
    try:
        with contextlib.closing(psycopg2.connect(**_PG_DSN)) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
                cur.fetchone()
        ok = True
    except Exception:
        ok = False
    return "postgres", ok, round(time.perf_counter() - t0, 4)


def _check_redis() -> Tuple[str, bool, float]:
    t0 = time.perf_counter()
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(_REDIS_TIMEOUT)
    try:
        sock.connect((_REDIS_HOST, _REDIS_PORT))
        ok = True
    except Exception:
        ok = False
    finally:
        sock.close()
    return "redis", ok, round(time.perf_counter() - t0, 4)


router = APIRouter(tags=["meta"])
_HEALTH_CHECKS: list[Callable[[], Tuple[str, bool, float]]] = [
    _check_postgres,
    _check_redis,
]


def _run_checks() -> dict[str, Any]:
    t0 = time.perf_counter()
    payload: Dict[str, Any] = {"status": "ok", "checks": {}, "duration": 0.0}
    for fn in _HEALTH_CHECKS:
        name, ok, dur = fn()
        payload["checks"][name] = {"ok": ok, "t": dur}
        if not ok:
            payload["status"] = "ng"
    payload["duration"] = round(time.perf_counter() - t0, 4)
    return payload


@router.get("/health", include_in_schema=False)
def health() -> JSONResponse:
    data = _run_checks()
    code = (
        status.HTTP_200_OK
        if data["status"] == "ok"
        else status.HTTP_503_SERVICE_UNAVAILABLE
    )
    return JSONResponse(data, code)


@router.api_route(
    "/healthz",
    methods=["GET", "HEAD"],
    include_in_schema=False,
    status_code=status.HTTP_204_NO_CONTENT,  # ← HEAD/GET どちらでも 204
)
def healthz(request: Request) -> Response:
    ok = _run_checks()["status"] == "ok"
    return Response(
        status_code=(
            status.HTTP_204_NO_CONTENT if ok else status.HTTP_503_SERVICE_UNAVAILABLE
        )
    )
