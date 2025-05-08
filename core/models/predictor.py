# =====================================================================
# ASSIST_KEY: 【core/model/predictor.py】
# =====================================================================
#
# 【概要】
#   直近データを使い “翌営業日終値” を 1 本推論し返す MVP Predictor。
#   永続化されたモデルはまだ無いので **毎回その場で再学習** して推論。
#
# 【主な役割】
#   - predict(symbol, start, end) → float
#   - 付随して最新メトリクスも返却し UI 側フィードバックに活用
#
# 【連携先・依存関係】
#   - core/data/loader.py          : 時系列取得
#   - core/feature/engineering.py  : 特徴量生成
#   - core/eval/metrics.py         : 評価
#   - sklearn.ensemble.GradientBoostingRegressor
#
# 【ルール遵守】
#   1) ファイル I/O は行わない（MVP は MemoryRepository のみ）
#   2) 返値 dict は JSON にダンプ可能なスカラ型
# ---------------------------------------------------------------------

from __future__ import annotations

import logging
from datetime import datetime
from typing import Dict

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor

from core.data.loader import load
from core.data.splitter import split_ts
from core.eval.metrics import evaluate
from core.feature.engineering import make_features

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------ #
# Public API
# ------------------------------------------------------------------ #
def predict(
    symbol: str,
    *,
    start: str | datetime,
    end: str | datetime,
) -> Dict[str, float]:
    """
    指定区間でモデルを再学習し、**end の翌営業日** を 1 点予測。

    Returns
    -------
    dict
        {
          "symbol": str,
          "predict_date": "YYYY-MM-DD",
          "predicted_close": float,
          "r2": …, "mae": …, …
        }
    """
    # -------------------------------------- #
    # 1. データ取得 & スプリット
    # -------------------------------------- #
    df_raw = load(symbol, start, end)
    train_df, valid_df, test_df = split_ts(df_raw)

    # -------------------------------------- #
    # 2. 特徴量
    # -------------------------------------- #
    X_train, y_train = make_features(pd.concat([train_df, valid_df]))
    X_test, y_test = make_features(test_df)  # ← “直近部分” を hold-out

    # -------------------------------------- #
    # 3. 学習 & テスト評価
    # -------------------------------------- #
    model = GradientBoostingRegressor(random_state=0)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    metrics = evaluate(y_test, y_pred)

    # -------------------------------------- #
    # 4. 直近 1 レコードを推論
    # -------------------------------------- #
    latest_window = df_raw.iloc[[-1]]  # DataFrame の末尾行 (ラベル保持)
    X_latest, _ = make_features(latest_window)  # y は不要
    next_close = float(model.predict(X_latest)[0])

    predict_date = pd.to_datetime(df_raw.index[-1]) + pd.tseries.offsets.BDay()

    logger.info(
        "[predictor] %s %s → %.2f  (r2=%.3f)",
        symbol,
        predict_date.date(),
        next_close,
        metrics["r2"],
    )

    return {
        "symbol": symbol,
        "predict_date": str(predict_date.date()),
        "predicted_close": next_close,
        **metrics,
    }
