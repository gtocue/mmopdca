# =====================================================================
# core/models/trainer.py
# ---------------------------------------------------------------------
#   GradientBoostingRegressor で翌営業日終値を予測する MVP Trainer
# =====================================================================

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Final, Literal, TypedDict, cast

import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor

from core.data.loader import load
from core.data.splitter import split_ts
from core.eval import evaluate                         # 共通メトリクス
from core.feature.engineering import make_features
from core.repository.factory import get_repo

logger = logging.getLogger(__name__)

# ────────────────────────────────────────────────────────────────────
# 戻り値の型
# ────────────────────────────────────────────────────────────────────
class TrainerResult(TypedDict):
    run_id: str
    r2: float
    mae: float
    rmse: float
    mape: float


# ────────────────────────────────────────────────────────────────────
# 損失関数エイリアス（旧 → 新 sklearn 名）
#   Literal で定義しておくと _LOSS_MAP[...] の戻り値も Literal 扱いになり
#   Pylance の「str は Literal に割り当て不可」エラーを回避できる
# ────────────────────────────────────────────────────────────────────
LegacyLoss = Literal["ls", "lad", "huber"]
SkLoss     = Literal["squared_error", "absolute_error", "huber"]

_LOSS_MAP: Final[dict[LegacyLoss, SkLoss]] = {
    "ls":   "squared_error",
    "lad":  "absolute_error",
    "huber": "huber",
}

# ────────────────────────────────────────────────────────────────────
# Public API
# ────────────────────────────────────────────────────────────────────
def train(
    symbol: str,
    *,
    start: str | datetime,
    end: str | datetime,
    train_ratio: float = 0.7,
    val_ratio: float = 0.1,
    loss: LegacyLoss = "ls",
) -> TrainerResult:
    """
    指定期間を使ってモデルを学習し、テストセットのスコアを返す。

    Returns
    -------
    TrainerResult
        ``{"run_id": ..., "r2": ..., "mae": ..., "rmse": ..., "mape": ...}``
    """
    # ── 1. データ取得 & 分割 ───────────────────────────────────
    df_raw = load(symbol, start, end)
    train_df, valid_df, test_df = split_ts(
        df_raw, train_ratio=train_ratio, val_ratio=val_ratio
    )

    # ── 2. 特徴量生成 ───────────────────────────────────────
    X_train, y_train = make_features(cast(pd.DataFrame, train_df))
    X_valid, y_valid = make_features(cast(pd.DataFrame, valid_df))
    X_test,  y_test  = make_features(cast(pd.DataFrame, test_df))

    # ── 3. モデル学習 ──────────────────────────────────────
    model = GradientBoostingRegressor(
        loss=_LOSS_MAP[loss],        # ← ここが Literal[SkLoss] 型
        random_state=42,
    )
    model.fit(
        pd.concat([X_train, X_valid]),
        pd.concat([y_train, y_valid]),
    )

    # ── 4. テスト評価 ──────────────────────────────────────
    y_pred  = model.predict(X_test)
    metrics = evaluate(y_test, y_pred)            # すべて Python float

    # ── 5. Repository へ保存 ────────────────────────────────
    run_id = f"{symbol}_{pd.Timestamp.utcnow():%Y%m%d%H%M%S}"
    repo   = get_repo("metrics")
    repo[run_id] = json.dumps(metrics)  # type: ignore[index]  実行時は OK

    logger.info(
        "[trainer] %s metrics=%s",
        run_id,
        {k: round(v, 4) for k, v in metrics.items()},
    )

    # ── 6. 結果返却 ─────────────────────────────────────────
    return TrainerResult(run_id=run_id, **metrics)
