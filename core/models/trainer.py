# =====================================================================
# ASSIST_KEY: 【core/model/trainer.py】
# =====================================================================
#
# 【概要】
#   シンプルな回帰モデル（GradientBoostingRegressor）で
#   翌営業日の終値を予測する MVP 用 Trainer。
#
# 【主な役割】
#   - train(symbol, start, end) → dict(result)
#   - パイプライン: load → split → make_features → fit → 評価 (r2 / MAE …)
#
# 【連携先・依存関係】
#   - core/data/loader.py           : 時系列取得
#   - core/data/splitter.py         : 時系列分割
#   - core/feature/engineering.py   : 特徴量生成
#   - sklearn, pandas, numpy
#
# 【ルール遵守】
#   1) 返却 dict は metrics_repo へそのまま保存できる形
#   2) heavy ML は避け、CPU 1 コア・<30 sec で完結
# ---------------------------------------------------------------------

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Dict, Literal

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import (
    mean_absolute_error,
    mean_absolute_percentage_error,
    mean_squared_error,
    r2_score,
)

from core.data.loader import load
from core.data.splitter import split_ts
from core.feature.engineering import make_features
from core.repository.factory import get_repo  # metrics 保存用

logger = logging.getLogger(__name__)

_METRICS = ["r2", "mae", "rmse", "mape"]


def _evaluate(y_true: pd.Series, y_pred: np.ndarray) -> Dict[str, float]:
    """共通メトリクス計算."""
    return {
        "r2": r2_score(y_true, y_pred),
        "mae": mean_absolute_error(y_true, y_pred),
        "rmse": mean_squared_error(y_true, y_pred, squared=False),
        "mape": mean_absolute_percentage_error(y_true, y_pred) * 100,
    }


def train(
    symbol: str,
    *,
    start: str | datetime,
    end: str | datetime,
    train_ratio: float = 0.7,
    val_ratio: float = 0.1,
    loss: Literal["ls", "lad", "huber"] = "ls",
) -> Dict[str, float]:
    """
    シンボルを指定してモデル学習 + 評価を実施。

    Returns
    -------
    result : dict
        {metric: value, ...} + run_id 等のメタ情報
    """
    # -----------------------------------------------------------------
    # 1. 取得 & split
    # -----------------------------------------------------------------
    df_raw = load(symbol, start, end)
    train_df, valid_df, test_df = split_ts(df_raw, train_ratio=train_ratio, val_ratio=val_ratio)

    # -----------------------------------------------------------------
    # 2. 特徴量生成
    # -----------------------------------------------------------------
    X_train, y_train = make_features(train_df)
    X_valid, y_valid = make_features(valid_df)
    X_test, y_test = make_features(test_df)

    # -----------------------------------------------------------------
    # 3. モデル学習
    # -----------------------------------------------------------------
    model = GradientBoostingRegressor(loss=loss, random_state=42)
    model.fit(
        pd.concat([X_train, X_valid]),
        pd.concat([y_train, y_valid]),
    )

    # -----------------------------------------------------------------
    # 4. 評価
    # -----------------------------------------------------------------
    y_pred = model.predict(X_test)
    metrics = _evaluate(y_test, y_pred)

    # -----------------------------------------------------------------
    # 5. 結果保存
    # -----------------------------------------------------------------
    run_id = f"{symbol}_{pd.Timestamp.utcnow().strftime('%Y%m%d%H%M%S')}"
    repo = get_repo("metrics")  # MemoryRepository / Redis … に差し替え可
    repo[run_id] = json.dumps(metrics)  # メモリ repo は JSON 文字列で格納

    logger.info("[trainer] %s  metrics=%s", run_id, {k: round(v, 4) for k, v in metrics.items()})

    return {"run_id": run_id, **metrics}
