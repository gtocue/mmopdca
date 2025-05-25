# =====================================================================
# core/models/predictor.py
# ---------------------------------------------------------------------
#   与えられた区間の OHLCV から “翌営業日 Close” を 1 本推論する MVP。
# =====================================================================

from __future__ import annotations

import logging
from datetime import datetime
from typing import TypedDict, cast

import pandas as pd
from pandas.tseries.offsets import BDay
from sklearn.ensemble import GradientBoostingRegressor

from core.data.loader import load
from core.data.splitter import split_ts
from core.eval import evaluate                     # ★ ここだけ修正
from core.feature.engineering import make_features

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------
# 戻り値の型
# ---------------------------------------------------------------------
class PredictResult(TypedDict):
    symbol: str
    predict_date: str
    predicted_close: float
    r2: float
    mae: float
    rmse: float
    mape: float


# ---------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------
def predict(
    symbol: str,
    *,
    start: str | datetime,
    end: str | datetime,
) -> PredictResult:
    """
    指定期間でモデルを学習し、**`end` の翌営業日** Close を 1 点推論し、
    主要メトリクスも合わせて返す。
    """

    # 1) データ取得 & スプリット
    df_raw = load(symbol, start, end)
    train_df, valid_df, test_df = split_ts(df_raw)

    # 2) 特徴量生成
    X_train, y_train = make_features(pd.concat([train_df, valid_df]))
    X_test, y_test = make_features(cast(pd.DataFrame, test_df))

    # 3) モデル学習 & 評価
    model = GradientBoostingRegressor(random_state=0)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    metrics = evaluate(y_test, y_pred)

    # 4) 直近 1 レコードを推論
    latest_window = df_raw.iloc[[-1]]
    X_latest, _ = make_features(latest_window)
    next_close = float(model.predict(X_latest)[0])

    predict_date = pd.to_datetime(df_raw.index[-1]) + BDay()

    logger.info(
        "[predictor] %s %s → %.2f  (r2=%.3f)",
        symbol,
        predict_date.date(),
        next_close,
        metrics["r2"],
    )

    # 5) 結果整形
    return PredictResult(
        symbol=symbol,
        predict_date=predict_date.strftime("%Y-%m-%d"),
        predicted_close=next_close,
        **metrics,  # r2 / mae / rmse / mape
    )
