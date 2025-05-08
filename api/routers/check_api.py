# =========================================================
# ASSIST_KEY: 【api/routers/check_api.py】
# =========================================================
#
# Check Router – Do フェーズ結果 (Parquet 等) を評価し、
#  1. /check に結果を保存
#  2. /metrics に指標を Upsert                ← ★追加
# ---------------------------------------------------------
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, HTTPException, Path, status

from core.check.check_executor import CheckExecutor
from core.repository.factory import get_repo
from core.schemas.check_schemas import CheckResult
from core.schemas.do_schemas import DoStatus

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/check", tags=["check"])

_do_repo = get_repo("do")
_check_repo = get_repo("check")
_metrics_repo = get_repo("metrics")   # ← ★ 追加


# ---------------------------------------------------------------------- #
# POST /check/{do_id}
# ---------------------------------------------------------------------- #
@router.post(
    "/{do_id}",
    response_model=CheckResult,
    status_code=status.HTTP_201_CREATED,
    summary="Do 結果を評価してメトリクス保存",
)
def create_check(
    do_id: str = Path(..., description="対象 Do ID (do-XXXX)"),
) -> CheckResult:
    # 1) Do レコード確認 ------------------------------------------------
    do_rec = _do_repo.get(do_id)
    if do_rec is None:
        raise HTTPException(404, "Do job not found")
    if do_rec["status"] != DoStatus.DONE:
        raise HTTPException(400, "Do job not finished yet")

    plan_id: str = do_rec["plan_id"]
    run_id: str = do_rec["do_id"]

    # 2) CheckExecutor 実行 --------------------------------------------
    try:
        result: CheckResult = CheckExecutor.run(plan_id, run_id)
    except Exception as exc:  # noqa: BLE001
        logger.error("[CheckAPI] CheckExecutor error: %s", exc, exc_info=True)
        raise HTTPException(500, f"CheckExecutor error: {exc}") from exc

    # 3) /check コレクションへ保存 -------------------------------------
    rec = result.model_dump(mode="json") | {
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    _check_repo.delete(result.id)
    _check_repo.create(result.id, rec)

    # 4) /metrics コレクションへ Upsert  ------------------------------- ★
    _metrics_repo.delete(run_id)
    _metrics_repo.create(
        run_id,
        {
            "run_id": run_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "r2": result.r2,
            "mae": result.mae,
            "rmse": result.rmse,
            "mape": result.mape,
        },
    )
    logger.info("[CheckAPI] metrics upsert run_id=%s r2=%.4f", run_id, result.r2)

    return result


# ---------------------------------------------------------------------- #
# GET /check/{check_id}
# ---------------------------------------------------------------------- #
@router.get(
    "/{check_id}",
    response_model=CheckResult,
    summary="単一 Check 結果取得",
)
def get_check(check_id: str) -> CheckResult:
    rec = _check_repo.get(check_id)
    if rec is None:
        raise HTTPException(404, "CheckResult not found")
    return CheckResult(**rec)


# ---------------------------------------------------------------------- #
# GET /check/
# ---------------------------------------------------------------------- #
@router.get(
    "/",
    response_model=List[CheckResult],
    summary="Check 結果一覧",
)
def list_check() -> List[CheckResult]:
    return [CheckResult(**r) for r in _check_repo.list()]
