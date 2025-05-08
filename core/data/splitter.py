# =====================================================================
# ASSIST_KEY: 【core/data/splitter.py】
# =====================================================================
#
# 【概要】
#   時系列 DataFrame を “順序を保ったまま” train / valid / test に
#   分割するユーティリティ。
#
# 【主な役割】
#   - split_ts(df, train_ratio, val_ratio) → (train, valid, test)
#   - 時系列を崩さず先頭から比率でスライス
#
# 【連携先・依存関係】
#   - core/data/loader.py で取得した生データ
#   - core/model/trainer.py で学習用に読み込み
#
# 【ルール遵守】
#   1) DataFrame/Series どちらも受け付け、戻り値は同型
#   2) 重複インデックスがある場合は raise
# ---------------------------------------------------------------------

from __future__ import annotations

from typing import Tuple

import pandas as pd


def _validate_index(df: pd.DataFrame | pd.Series) -> None:
    idx = df.index
    if not isinstance(idx, pd.DatetimeIndex):
        raise TypeError("index must be DatetimeIndex")
    if not idx.is_monotonic_increasing:
        raise ValueError("index must be sorted ascending")
    if idx.has_duplicates:  # pragma: no cover
        raise ValueError("index has duplicated timestamps")


def split_ts(
    data: pd.DataFrame | pd.Series,
    *,
    train_ratio: float = 0.7,
    val_ratio: float = 0.1,
) -> Tuple[pd.DataFrame | pd.Series, ...]:
    """
    時系列データを chronological に 3 分割する。

    Parameters
    ----------
    data : pd.DataFrame | pd.Series
        対象データ（DatetimeIndex 必須）
    train_ratio : float, default 0.7
    val_ratio : float, default 0.1
        test_ratio = 1 - train_ratio - val_ratio で自動算出

    Returns
    -------
    train, valid, test : 同型 tuple
    """
    _validate_index(data)

    if not (0 < train_ratio < 1) or not (0 <= val_ratio < 1):
        raise ValueError("ratios must be within (0,1)")

    n = len(data)
    n_train = int(n * train_ratio)
    n_val = int(n * val_ratio)
    # test は残り全部
    train = data.iloc[:n_train]
    valid = data.iloc[n_train : n_train + n_val]  # noqa: E203
    test = data.iloc[n_train + n_val :]
    return train, valid, test
