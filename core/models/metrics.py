# =====================================================================
# ASSIST_KEY: 【core/eval/metrics.py】
# =====================================================================
#
# 【概要】
#   モデル評価で共通利用するスコア関数群を一本化。
#
# 【主な役割】
#   - r2 / MAE / RMSE / MAPE を計算する utility
#   - 1 か所に集約して重複・実装揺れを防止
#
# 【連携先・依存関係】
#   - core/model/trainer.py     : 学習後の評価
#   - core/model/predictor.py   : 推論結果の後検証 (任意)
#
# 【ルール遵守】
#   1) sk-learn / numpy 以外の外部依存を追加しない
#   2) 新規メトリクスを足す際は __all__ にも追記
# ---------------------------------------------------------------------

from __future__ import annotations

from typing import Dict

import numpy as np

__all__ = ["evaluate"]


# ------------------------------------------------------------------ #
# Public API
# ------------------------------------------------------------------ #
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


def evaluate(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """共通メトリクス計算."""

    r2 = _r2_score(y_true, y_pred)
    mae = _mae(y_true, y_pred)
    rmse = _rmse(y_true, y_pred)
    mape = _mape(y_true, y_pred)

    return {"r2": r2, "mae": mae, "rmse": rmse, "mape": mape}
