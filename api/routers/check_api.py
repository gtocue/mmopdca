# =========================================================
# ASSIST_KEY: このファイルは【api/routers/check_api.py】に位置するユニットです
# =========================================================
#
# 【概要】
#   CheckRouter – Do の Parquet を評価し、メトリクスを永続化
#
# ---------------------------------------------------------
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, HTTPException, Path, status

from core.check.check_executor import CheckExecutor
from core.repository.factory import get_repo
from core.schemas.check_schemas import CheckResult
from core.schemas.do_schemas import DoStatus

router = APIRouter(prefix="/check", tags=["check"])

_do_repo = get_repo("do")
_check_repo = get_repo("check")

# ──────────────────────────────────────────────
# POST /check/{do_id}
# ──────────────────────────────────────────────
@router.post(
    "/{do_id}",
    response_model=CheckResult,
    status_code=status.HTTP_201_CREATED,
)
def create_check(
    do_id: str = Path(..., description="対象 Do ID"),
) -> CheckResult:
    # 1) Do レコード確認
    do_rec = _do_repo.get(do_id)
    if do_rec is None:
        raise HTTPException(404, "Do not found")
    if do_rec["status"] != DoStatus.DONE:
        raise HTTPException(400, "Do not finished yet")

    plan_id = do_rec["plan_id"]
    run_id = do_rec["do_id"].split("__")[-1] if "__" in do_rec["do_id"] else do_rec["do_id"]

    # 2) CheckExecutor 実行
    try:
        result = CheckExecutor.run(plan_id, run_id)
    except Exception as exc:
        raise HTTPException(500, f"CheckExecutor error: {exc}") from exc

    # 3) 永続化
    rec = result.model_dump(mode="json")
    rec["created_at"] = datetime.now(timezone.utc).isoformat()
    _check_repo.create(result.id, rec)

    return result

# ──────────────────────────────────────────────
# GET /check/{check_id}
# ──────────────────────────────────────────────
@router.get("/{check_id}", response_model=CheckResult)
def get_check(check_id: str) -> CheckResult:
    rec = _check_repo.get(check_id)
    if rec is None:
        raise HTTPException(404, "CheckResult not found")
    return CheckResult(**rec)

# ──────────────────────────────────────────────
# GET /check/
# ──────────────────────────────────────────────
@router.get("/", response_model=List[CheckResult])
def list_check() -> List[CheckResult]:
    return [CheckResult(**r) for r in _check_repo.list()]
