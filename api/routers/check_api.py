# =========================================================
# ASSIST_KEY: このファイルは【api/routers/check_api.py】に位置するユニットです
# =========================================================
#
# 【概要】
#   CheckRouter ― Do 結果を評価してメトリクスを保存する
#
# ---------------------------------------------------------

from __future__ import annotations

import uuid
from datetime import datetime
from typing import List

from fastapi import APIRouter, HTTPException, Path, status

from core.schemas.check_schemas import CheckResult        # pydantic スキーマ
from core.repository.factory import get_repo

router = APIRouter(prefix="/check", tags=["check"])

# Do / Check 用リポジトリ
_do_repo    = get_repo("do")       # status, result が入っている
_check_repo = get_repo("check")    # ここに評価結果を保存


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
    # 1) Do 結果をロード
    do_rec = _do_repo.get(do_id)
    if do_rec is None:
        raise HTTPException(404, "Do not found")
    if do_rec["status"] != "DONE":
        raise HTTPException(400, "Do not finished yet")

    # 2) ごく簡易な評価ロジック（r2 > 0.8 合格）
    r2 = do_rec["result"]["metrics"]["r2"]
    threshold = 0.8
    passed = r2 >= threshold

    check = CheckResult(
        id=f"check-{uuid.uuid4().hex[:8]}",
        do_id=do_id,
        created_at=datetime.utcnow(),
        report={"r2": r2, "threshold": threshold, "pass": passed},
    )

    # 3) 保存
    _check_repo.create(check.id, check.model_dump(mode="json"))
    return check


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
