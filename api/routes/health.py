# =====================================================================
# ASSIST_KEY: 【api/routes/health.py】 – service-level Health Check
# =====================================================================
from __future__ import annotations
from fastapi import APIRouter, Response, status

router = APIRouter(tags=["meta"])

@router.get("/health", include_in_schema=False)
def health() -> dict[str, str]:
    """アプリケーションの生存確認 (JSON)"""
    return {"status": "ok"}

@router.get(
    "/healthz",
    include_in_schema=False,
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def healthz() -> Response:
    """K8s 用 readinessProbe (204 Only)"""
    return Response(status_code=status.HTTP_204_NO_CONTENT)
