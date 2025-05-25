"""
core.eval.metrics
-----------------
モデル評価で共通利用するメトリクス計算ユーティリティ。

* 返却値は必ず **Python float**（NumPy スカラーや ndarray は残さない）
* 追加メトリクスを実装したら __all__ に追記する
"""

from __future__ import annotations

from typing import Any, Dict, SupportsFloat, Union, cast

import numpy as np
import numpy.typing as npt
from sklearn.metrics import (
    mean_absolute_error,
    mean_absolute_percentage_error,
    mean_squared_error,
    r2_score,
)

__all__: list[str] = ["evaluate"]

# ------------------------------------------------------------------ #
# 型エイリアス（list・pd.Series なども許容）
# ------------------------------------------------------------------ #
ArrayLike = Union[
    npt.NDArray[np.floating],
    npt.NDArray[np.integer],
    npt.ArrayLike,
]

# ------------------------------------------------------------------ #
# 内部ヘルパー：なんでも Python float に正規化
# ------------------------------------------------------------------ #
def _to_float(x: Any) -> float:  # noqa: D401
    """
    * NumPy スカラー      → float  
    * 0-d / 要素 1 ndarray → float  
    * それ以外の ndarray  → ValueError
    """
    # ndarray 系
    if isinstance(x, np.ndarray):
        if x.ndim == 0 or x.size == 1:        # 0-d または要素 1
            return float(x.item())
        raise ValueError("metric result is not a scalar array")

    # Python スカラー / NumPy スカラー
    return float(cast(SupportsFloat, x))


# ------------------------------------------------------------------ #
# Public API
# ------------------------------------------------------------------ #
def evaluate(y_true: ArrayLike, y_pred: ArrayLike) -> Dict[str, float]:
    """
    r2 / MAE / RMSE / MAPE を計算して ``Dict[str, float]`` を返す。
    受け取った入力は list・Series など何でも OK（内部で ndarray 化）。
    """
    # 何が来ても 1-D float ndarray へ整形
    y_true_arr = np.asarray(y_true, dtype=float).ravel()
    y_pred_arr = np.asarray(y_pred, dtype=float).ravel()

    return {
        "r2":   _to_float(r2_score(y_true_arr, y_pred_arr)),
        "mae":  _to_float(mean_absolute_error(y_true_arr, y_pred_arr)),
        "rmse": _to_float(mean_squared_error(y_true_arr, y_pred_arr, squared=False)),
        "mape": _to_float(mean_absolute_percentage_error(y_true_arr, y_pred_arr) * 100.0),
    }
