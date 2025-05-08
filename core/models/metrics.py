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
from sklearn.metrics import (
    mean_absolute_error,
    mean_absolute_percentage_error,
    mean_squared_error,
    r2_score,
)

__all__ = ["evaluate"]

# ------------------------------------------------------------------ #
# Public API
# ------------------------------------------------------------------ #
def evaluate(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """
    共通メトリクス計算。

    Parameters
    ----------
    y_true, y_pred : array-like
        実測値 / 予測値

    Returns
    -------
    dict
        {"r2": …, "mae": …, "rmse": …, "mape": …}
    """
    return {
        "r2": r2_score(y_true, y_pred),
        "mae": mean_absolute_error(y_true, y_pred),
        "rmse": mean_squared_error(y_true, y_pred, squared=False),
        "mape": mean_absolute_percentage_error(y_true, y_pred) * 100,
    }
