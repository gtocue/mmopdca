# =========================================================
# core/do/coredo_executor.py
# ---------------------------------------------------------
# Do フェーズ ― MVP 実装
#   1. 価格取得      : Yahoo-Finance (yfinance 0.2.*)
#   2. 指標計算      : SMA / EMA / RSI
#   3. 予測モデル    : 線形回帰で「翌営業日の終値」を推定
#
# 【ルール 2025-04-27】
#   • Plan-ID × run_no で何度でも実行できる
#   • params は dict[str, Any] 固定
#
# NOTE
#   ◦ 古い scikit-learn 互換で RMSE を手計算 fallback
#   ◦ yfinance が MultiIndex を返した場合は flatten
#   ◦ 返却する date は「予測対象日」＝ index + 1 BusinessDay
#     ── 市場独自の休場日は params["holidays"] で拡張可 (下記参照)
# =========================================================
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Callable, List, Tuple

import numpy as np
import pandas as pd
import yfinance as yf
from pandas.tseries.offsets import BDay, CustomBusinessDay
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# ────────────────────────────────────────────────
# Public API
# ────────────────────────────────────────────────
def run_do(plan_id: str, params: dict[str, Any]) -> dict[str, Any]:
    """
    Execute **one** Do-phase run and return JSON-serialisable dict.

    必須キー
    --------
    symbol : str
    start  : "YYYY-MM-DD"
    end    : "YYYY-MM-DD"
    run_no : int

    任意キー
    --------
    indicators : list[dict]   # 各要素 {name: SMA|EMA|RSI, window:int}
    holidays   : list[str]    # 市場固有の休場日 ["YYYY-MM-DD", ...]
    """
    symbol, start, end, ind_cfg, run_no, holidays = _parse_params(params)
    run_id = f"{plan_id}__{run_no:04d}"
    logger.info("[Do] ▶ run_id=%s  %s  %s→%s", run_id, symbol, start, end)

    # 1. price ----------------------------------------------------------
    df = _download_prices(symbol, start, end)

    # 2. indicators -----------------------------------------------------
    df = _add_indicators(df, ind_cfg)
    if len(df) < 30:
        raise RuntimeError("Not enough rows (≥30) after preprocessing")

    # 3. model ----------------------------------------------------------
    preds, model, feature_cols, metrics = _train_and_predict(df)

    # 4. predictions with +1 Business Day -------------------------------
    bday = _make_bday_offset(holidays)
    target_dates = (df.index + bday).strftime("%Y-%m-%d")

    last30: List[dict[str, Any]] = [
        {"date": d, "price": float(round(p, 4))}
        for d, p in zip(target_dates[-30:], preds[-30:])
    ]

    # 5. build response -------------------------------------------------
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
        "predictions": last30,   # list[{"date": str, "price": float}]
    }


# ────────────────────────────────────────────────
# helpers
# ────────────────────────────────────────────────
def _parse_params(
    params: dict[str, Any],
) -> Tuple[str, str, str, List[dict[str, Any]], int, List[str]]:
    def _req(key: str) -> Any:
        if key not in params:
            raise RuntimeError(f"missing required param: '{key}'")
        return params[key]

    symbol: str = str(_req("symbol"))
    start: str = str(_req("start"))
    end: str = str(_req("end"))
    run_no: int = int(_req("run_no"))

    indicators = params.get("indicators") or [{"name": "SMA", "window": 5}]
    if not isinstance(indicators, list):
        raise RuntimeError("indicators must be list[dict]")
    for ind in indicators:
        if "name" not in ind:
            raise RuntimeError("indicator item requires 'name'")

    holidays: List[str] = params.get("holidays", [])  # optional

    return symbol, start, end, indicators, run_no, holidays


def _make_bday_offset(holidays: List[str]):
    """
    Return a (Custom)BusinessDay(+1) to shift index safely.

    * デフォルト → 土日除外のみ (BDay)
    * holidays が渡されたらその日付も除外 (CustomBusinessDay)
    """
    if holidays:
        # TODO: 外部カレンダー設定に移動する
        return CustomBusinessDay(holidays=holidays)
    return BDay()


def _download_prices(symbol: str, start: str, end: str) -> pd.DataFrame:
    df = yf.download(
        symbol,
        start=start,
        end=end,
        progress=False,
        auto_adjust=False,
        group_by="column",
    )
    if df.empty:
        raise RuntimeError(f"No price data for '{symbol}'")

    # ─── flatten MultiIndex ─────────────────────────────────
    if isinstance(df.columns, pd.MultiIndex):
        # pattern-A: (field, ticker)
        try:
            df = df.xs(symbol, level=1, axis=1, drop_level=True)
        except KeyError:
            # pattern-B: (ticker, field)
            try:
                df = df.xs(symbol, level=0, axis=1, drop_level=True)
            except KeyError:
                df.columns = ["_".join(map(str, c)) for c in df.columns]
    # ────────────────────────────────────────────────

    df.columns = [str(c).capitalize() for c in df.columns]
    if "Adj close" in df.columns:
        df = df.rename(columns={"Adj close": "Adj Close"})

    return (
        df[["Open", "High", "Low", "Close", "Adj Close", "Volume"]]
        .dropna(subset=["Close"])
        .copy()
    )


# ---------- indicators ----------
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

        if col not in df.columns:
            df[col] = func(close, win)

    if "SMA_5" not in df.columns:  # safety-net
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

    # -- RMSE: fallback for old scikit-learn -----------------
    try:
        rmse = mean_squared_error(y, preds, squared=False)
    except TypeError:
        rmse = np.sqrt(mean_squared_error(y, preds))
    # --------------------------------------------------------

    r2 = float(np.corrcoef(y, preds)[0, 1] ** 2)

    logger.info("[Do] ✓ rows=%d  r2=%.4f  rmse=%.4f", len(df), r2, rmse)

    return preds, model, feature_cols, {"r2": r2, "rmse": float(round(rmse, 6))}
