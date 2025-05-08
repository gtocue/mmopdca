# =====================================================================
# ASSIST_KEY: 【core/feature/engineering.py】
# =====================================================================
#
# 【概要】
#   時系列株価 DataFrame から学習用特徴量を作成するユーティリティ。
#
# 【主な役割】
#   - make_features(df, lags, ma_windows) → (X, y)
#   - lags  : 前日差分などの自己回帰系列
#   - MAs   : 移動平均 (SMA)・ボラティリティなどのテクニカル指標
#
# 【連携先・依存関係】
#   - core/data/loader.py           : 原データ取得
#   - core/model/trainer.py         : モデル学習時に呼び出し
#
# 【ルール遵守】
#   1) 元 DataFrame は「Close」を含むこと
#   2) 返す X, y は同インデックス（NaN が出た行は自動 drop）
# ---------------------------------------------------------------------

from __future__ import annotations

import logging
from typing import Iterable, Tuple

import pandas as pd

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------ #
# 公開 API
# ------------------------------------------------------------------ #
def make_features(
    df: pd.DataFrame,
    *,
    lags: Iterable[int] = (1, 2, 3, 5, 10),           # TODO: 外部設定へ
    ma_windows: Iterable[int] = (5, 10, 20, 60, 120),  # TODO: 外部設定へ
) -> Tuple[pd.DataFrame, pd.Series]:
    """
    価格 DataFrame を特徴量行列 / 目的変数に変換する。

    Parameters
    ----------
    df : pd.DataFrame
        列に "Close" を含む価格系列
    lags : iterable of int, default (1,2,3,5,10)
        差分ラグ（日数）
    ma_windows : iterable of int, default (5,10,20,60,120)
        単純移動平均（日数）

    Returns
    -------
    X : pd.DataFrame
        特徴量行列
    y : pd.Series
        翌営業日の終値 (Close[t+1])
    """
    if "Close" not in df.columns:
        raise ValueError('"Close" column is required')

    X = pd.DataFrame(index=df.index)

    # --- lag features -------------------------------------------------
    for lag in lags:
        X[f"lag_{lag}"] = df["Close"].shift(lag)

    # --- moving averages ---------------------------------------------
    for win in ma_windows:
        X[f"sma_{win}"] = df["Close"].rolling(window=win).mean()
        X[f"vol_{win}"] = df["Close"].rolling(window=win).std()

    # --- percentage returns ------------------------------------------
    X["returns_1d"] = df["Close"].pct_change(1)
    X["returns_5d"] = df["Close"].pct_change(5)

    # --- target (next-day close) -------------------------------------
    y = df["Close"].shift(-1).rename("target")

    # --- align / drop NaNs -------------------------------------------
    data = pd.concat([X, y], axis=1).dropna()
    X_clean = data.drop(columns="target")
    y_clean = data["target"]

    logger.info(
        "[engineering] features=%d  samples=%d  dropped=%d",
        X_clean.shape[1],
        len(X_clean),
        len(df) - len(X_clean),
    )
    return X_clean, y_clean
