# =========================================================
# ASSIST_KEY: このファイルは【core/check/check_executor.py】に位置するユニットです
# =========================================================
#
# 【概要】
#   このユニットは “CheckExecutor” として、
#   Do フェーズの予測 Parquet を読み込み、メトリクス計算と
#   合否判定を行ったうえで CheckResult を生成します。
#
# 【主な役割】
#   - load_predictions() で DataFrame 読込
#   - load_meta()        で MetaInfo 取得
#   - MAPE / RMSE / R² を計算
#   - 合否判定 → CheckResult を返却
#
# 【連携先・依存関係】
#   - core/common/io_utils.py            … Parquet & meta I/O
#   - core/schemas.check_schemas.py      … CheckResult, CheckReport
#   - core/schemas.meta_schemas.py       … MetricSpec, MetaInfo
#
# 【ルール遵守】
#   1) print() 禁止 → logging.debug() を使用
#   2) メイン銘柄 "Close_main" などのハードコード禁止
# ---------------------------------------------------------
from __future__ import annotations

import logging
import math
import uuid
from typing import Any, Dict

from core.common.io_utils import load_predictions, load_meta
from core.schemas.check_schemas import CheckResult, CheckReport
from core.schemas.meta_schemas import MetaInfo
from core.constants import SUPPORTED_METRICS

logger = logging.getLogger(__name__)

# --------------------------------------------------
# データフレームライブラリ (polars > pandas 優先)
# --------------------------------------------------
try:
    import polars as pl  # type: ignore

    _DF_LIB = "polars"
except ModuleNotFoundError:  # pragma: no cover
    _DF_LIB = "pandas"


# --------------------------------------------------
# メトリクス計算ユーティリティ
# --------------------------------------------------
def _mape(y_true, y_pred) -> float:
    return float((abs((y_true - y_pred) / y_true)).mean()) * 100.0


def _rmse(y_true, y_pred) -> float:
    return float(math.sqrt(((y_true - y_pred) ** 2).mean()))


def _r2(y_true, y_pred) -> float:
    mean_y = float(y_true.mean())
    ss_tot = float(((y_true - mean_y) ** 2).sum())
    ss_res = float(((y_true - y_pred) ** 2).sum())
    return 1.0 - ss_res / ss_tot if ss_tot != 0 else 0.0


_METRIC_FUNCS = {
    "mape": _mape,
    "rmse": _rmse,
    "r2": _r2,
}


# --------------------------------------------------
# CheckExecutor
# --------------------------------------------------
class CheckExecutor:
    """
    Do → Check の QA プロセスをカプセル化。
    """

    @classmethod
    def run(cls, plan_id: str, run_id: str) -> CheckResult:
        """
        予測 Parquet と meta.json を読み込み、各指標を計算して
        CheckResult を返す。
        """
        df = load_predictions(plan_id, run_id)
        meta_dict: Dict[str, Any] = load_meta(plan_id, run_id)
        meta = MetaInfo.model_validate(meta_dict)

        logger.debug("Loaded predictions rows=%d", len(df))
        logger.debug("Loaded meta: %s", meta)

        # --- 真値 / 予測値 Series 取得 ---------------------------------
        if _DF_LIB == "polars":
            y_true = df["y_true"]
            y_pred = df["y_pred"]
        else:  # pandas
            y_true = df["y_true"]
            y_pred = df["y_pred"]

        # --- メトリクス計算 & 閾値チェック ------------------------------
        report_dict: Dict[str, Any] = {}
        for spec in meta.metrics:
            if spec.name not in SUPPORTED_METRICS:
                logger.warning("Unsupported metric: %s (skip)", spec.name)
                continue

            value = _METRIC_FUNCS[spec.name](y_true, y_pred)
            passed = (
                value <= spec.threshold
                if spec.name != "r2"
                else value >= spec.threshold
            )

            report_dict[spec.name] = value
            report_dict[f"{spec.name}_threshold"] = spec.threshold
            report_dict[f"{spec.name}_passed"] = passed

        # --- 合否 (全指標をクリアしたら PASS) ---------------------------
        overall_passed = all(v for k, v in report_dict.items() if k.endswith("_passed"))

        check_report = CheckReport(
            r2=report_dict.get("r2", 0.0),
            threshold=report_dict.get("r2_threshold", 0.0),
            passed=report_dict.get("r2_passed", overall_passed),
        )

        check_result = CheckResult(
            id=f"check_{uuid.uuid4().hex[:8]}",
            do_id=run_id,
            created_at=meta.created_at,  # メタ生成時刻を流用
            report=check_report,
        )

        logger.debug("CheckResult: %s", check_result)
        return check_result


# 公開シンボル
__all__ = ["CheckExecutor"]
