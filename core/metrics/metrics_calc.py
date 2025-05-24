# =========================================================
# ASSIST_KEY: このファイルは【core/metrics/metrics_calc.py】に位置するユニットです
# =========================================================
#
# 【概要】
#   このユニットは MetricsCalc として、
#   予測結果 vs 実測値の評価指標(R², MAE, RMSE, MAPE ほか)を
#   計算し、後続ユニット(API/Prometheus Export 等)が再利用できる
#   Python 関数を提供します。
#
# 【主な役割】
#   - Do フェーズが生成した Parquet/CSV をロード (外部 I/O は呼び出し元)
#   - ndarray/Series から評価指標を計算し dict で返却
#   - 計算アルゴリズムは sklearn.metrics / numpy ベースで統一
#
# 【連携先・依存関係】
#   - 他ユニット :
#       ・api/routers/metrics_api.py (評価値取得 API)
#       ・core.repository.metrics_repo (評価値の永続化)
#   - 外部設定 :
#       ・pdca_data/<run_id>/pred.parquet 等 (ストレージ仕様 TBD)
#
# 【ルール遵守】
#   1) メイン銘柄 "Close_main" / "Open_main" は直接扱わない
#   2) 市場名は "Close_Nikkei_225" / "Open_SP500" のように suffix で区別
#   3) **全体コード** を返却（スニペットではなくファイルの完成形）
#   4) ファイル冒頭に必ず本ヘッダーを残すこと
#   5) 機能削除や breaking change は事前相談（原則 “追加” のみ）
#   6) pdca_data[...] キーに統一し、グローバル変数直書き禁止
#
# 【注意事項】
#   - ハードコード値を見つけたら「TODO: 外部設定へ」のコメントを添付
#   - インターフェース変更時は docs/ARCH.md を必ず更新
#   - 型安全重視 (Pydantic / typing)・ハルシネーション厳禁
# ---------------------------------------------------------

"""Metric calculation helper.

中央集権的な評価指標ロジックを 1 箇所に閉じ込めることで
・計算定義のブレ防止
・Prometheus / UI / レポートでの再利用性向上
を狙う。
"""

from __future__ import annotations

import logging
from typing import Iterable, Dict

import numpy as np
import pandas as pd


logger = logging.getLogger(__name__)
if not logger.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("[%(levelname)s] %(name)s: %(message)s"))
    logger.addHandler(_h)
logger.setLevel(logging.INFO)

__all__ = ["calc_metrics"]


# ---------------------------------------------------------------------------
# internal metric helpers (numpy only)
# ---------------------------------------------------------------------------

def _r2_score(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    return 1.0 - ss_res / ss_tot if ss_tot != 0 else 0.0


def _mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.mean(np.abs(y_true - y_pred)))


def _rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))


def _mape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    with np.errstate(divide="ignore", invalid="ignore"):
        ape = np.abs((y_true - y_pred) / y_true)
        ape = ape[~np.isinf(ape)]
        return float(np.mean(ape)) * 100 if ape.size else float("nan")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def calc_metrics(
    actual: Iterable[float] | pd.DataFrame,
    pred: Iterable[float] | None = None,
    *,
    actual_col: str = "actual",
    pred_col: str = "pred",
) -> Dict[str, float]:
    """Calculate evaluation metrics from arrays or a DataFrame."""

    if pred is None:
        if not isinstance(actual, pd.DataFrame):
            raise TypeError("DataFrame expected when ``pred`` is None")
        df = actual
        if actual_col not in df.columns or pred_col not in df.columns:
            missing = {c for c in (actual_col, pred_col) if c not in df.columns}
            raise KeyError(f"Required column(s) missing: {missing}")
        y_true = df[actual_col].to_numpy(dtype=float)
        y_pred = df[pred_col].to_numpy(dtype=float)
    else:
        y_true = np.asarray(list(actual), dtype=float)
        y_pred = np.asarray(list(pred), dtype=float)

    if y_true.size == 0:
        raise ValueError("Input data is empty – cannot compute metrics.")

    r2 = _r2_score(y_true, y_pred)
    mae = _mae(y_true, y_pred)
    rmse = _rmse(y_true, y_pred)
    mape = _mape(y_true, y_pred)

    metrics = {
        "r2": round(float(r2), 4),
        "mae": round(float(mae), 4),
        "rmse": round(float(rmse), 4),
        "mape": round(float(mape), 2),
    }

    logger.info(
        "[MetricsCalc] r2=%.4f mae=%.4f rmse=%.4f mape=%.2f%%",
        metrics["r2"],
        metrics["mae"],
        metrics["rmse"],
        metrics["mape"],
    )
    return metrics
