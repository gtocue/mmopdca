# =========================================================
# core/do/coredo_executor.py
# =========================================================
#
# Do フェーズ ― MVP 実装
#   1. 価格取得      : Yahoo Finance
#   2. 指標計算      : SMA / EMA / RSI（プラグイン置換しやすい構造）
#   3. 予測モデル    : 線形回帰で「翌日終値」を推定
#
# 【ルール 2025-04-27】
#   7) Plan-ID × run_no で “何回でも” 実行できる設計
#      └ 呼び出し側（DoCreateRequest）が **run_no:int** を必須で送る
#      └ run_id = f"{plan_id}__{run_no:04d}"
#   8) params は将来拡張のため **dict[str, Any]** 固定
# ---------------------------------------------------------

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Callable, List, Tuple

import numpy as np
import pandas as pd
import yfinance as yf
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# ────────────────────────────────────────────────
# Public API
# ────────────────────────────────────────────────
def run_do(plan_id: str, params: dict[str, Any]) -> dict[str, Any]:
    """
    Do フェーズを 1 回実行し結果を JSON 互換 dict で返す。

    Parameters
    ----------
    plan_id : str
        呼び出し元 Plan の ID
    params  : dict[str, Any]
        {
          "run_no"    : int,               # ★必須
          "symbol"    : str,
          "start"     : "YYYY-MM-DD",
          "end"       : "YYYY-MM-DD",
          "indicators": [                  # optional
              {"name": "SMA", "window": 5},
              {"name": "EMA", "window":20}
          ]
        }
    """
    symbol, start, end, ind_cfg, run_no = _parse_params(params)
    run_id = f"{plan_id}__{run_no:04d}"

    logger.info("[Do] ▶ run_id=%s  %s  %s→%s", run_id, symbol, start, end)

    # 1. price download -------------------------------------------------
    df = _download_prices(symbol, start, end)

    # 2. indicator engineering -----------------------------------------
    df = _add_indicators(df, ind_cfg)
    if len(df) < 30:
        raise RuntimeError("Not enough rows (≥30) after preprocessing")

    # 3. training / inference ------------------------------------------
    preds, model, feature_cols, metrics = _train_and_predict(df)

    # 4. build response -------------------------------------------------
    last30: List[Tuple[str, float]] = list(
        zip(
            df.index[-30:].strftime("%Y-%m-%d").tolist(),
            preds[-30:].round(4).tolist(),
        )
    )

    return {
        "run_id": run_id,
        "created_at": datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "summary": {
            "rows": int(len(df)),
            "features_used": feature_cols,
            "coef": np.round(model.coef_, 6).tolist(),
            "intercept": float(round(model.intercept_, 6)),
        },
        "metrics": metrics,
        "predictions": last30,  # [[date, value], ...] (最新30件)
    }


# ────────────────────────────────────────────────
# helpers
# ────────────────────────────────────────────────
def _parse_params(
    params: dict[str, Any],
) -> Tuple[str, str, str, List[dict[str, Any]], int]:
    """必須キー検査と型・デフォルト補完"""

    def _req(key: str) -> Any:
        if key not in params:
            raise RuntimeError(f"missing required param: '{key}'")
        return params[key]

    symbol: str = str(_req("symbol"))
    start: str = str(_req("start"))
    end: str = str(_req("end"))
    run_no: int = int(_req("run_no"))  # ★必須

    indicators = params.get("indicators") or [{"name": "SMA", "window": 5}]
    if not isinstance(indicators, list):
        raise RuntimeError("indicators must be list[dict]")

    for ind in indicators:
        if "name" not in ind:
            raise RuntimeError("indicator item requires 'name'")

    return symbol, start, end, indicators, run_no


def _download_prices(symbol: str, start: str, end: str) -> pd.DataFrame:
    df = yf.download(symbol, start=start, end=end, progress=False, auto_adjust=False)
    if df.empty:
        raise RuntimeError(f"No price data for '{symbol}'")
    # 明示列のみ残し null Close 行は除外
    return (
        df[["Open", "High", "Low", "Close", "Adj Close", "Volume"]]
        .dropna(subset=["Close"])
        .copy()
    )


# ---------- indicator builders ----------
def _sma(close: pd.Series, win: int) -> pd.Series:
    return close.rolling(win, min_periods=win).mean()


def _ema(close: pd.Series, win: int) -> pd.Series:
    return close.ewm(span=win, adjust=False).mean()


def _rsi(close: pd.Series, win: int) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(win, min_periods=win).mean()
    loss = -delta.clip(upper=0).rolling(win, min_periods=win).mean()
    rs = gain / loss.replace(0, 1e-9)
    return 100 - (100 / (1 + rs))


_IND_FUNCS: dict[str, Callable[[pd.Series, int], pd.Series]] = {
    "SMA": _sma,
    "EMA": _ema,
    "RSI": _rsi,
}


def _add_indicators(df: pd.DataFrame, cfg: List[dict[str, Any]]) -> pd.DataFrame:
    close = df["Close"]
    for ind in cfg:
        name = ind["name"].upper()
        win = int(ind.get("window", 5))
        col = f"{name}_{win}"

        func = _IND_FUNCS.get(name)
        if func is None:
            raise RuntimeError(f"Unsupported indicator '{name}'")

        if col not in df.columns:  # 冪等
            df[col] = func(close, win)

    # safety-net：最低限 SMA_5 は追加
    if "SMA_5" not in df.columns:
        df["SMA_5"] = _sma(close, 5)

    return df.dropna()


def _train_and_predict(
    df: pd.DataFrame,
) -> Tuple[np.ndarray, LinearRegression, List[str], dict[str, float]]:
    df = df.copy()
    df["target"] = df["Close"].shift(-1)
    df = df.dropna()

    feature_cols = [c for c in df.columns if c.startswith(("SMA_", "EMA_", "RSI_"))]
    if not feature_cols:
        raise RuntimeError("No usable features – add SMA / EMA / RSI indicators")

    X = df[feature_cols].values
    y = df["target"].values

    model = LinearRegression()
    model.fit(X, y)
    preds = model.predict(X)

    metrics = {
        "r2": float(round(r2_score(y, preds), 6)),
        "rmse": float(round(mean_squared_error(y, preds, squared=False), 6)),
    }

    logger.info(
        "[Do] ✓ rows=%d  r2=%.4f  rmse=%.4f",
        len(df),
        metrics["r2"],
        metrics["rmse"],
    )
    return preds, model, feature_cols, metrics
