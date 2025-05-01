# =====================================================================
# core/do/coredo_executor.py
# =====================================================================
#
# Do フェーズ ― MVP ＋ “Spot-Checkpoint” 拡張版
#
# 1. 価格取得        : IDataSource (既定は yfinance fallback)
# 2. インジケータ計算 : SMA / EMA / RSI
# 3. 予測モデル      : 線形回帰で「翌営業日の終値」を推定
# 4. チェックポイント : epoch 毎に JSON を保存し、SIGTERM 後に自動再開
#
#   * run_do(plan_id, params_dict) ― params は dict[str, Any]
#   * ONSPOT_INSTANCE=true のワーカーは “いつ落ちても良い” 前提
#   * Celery の task_acks_late=True と組み合わせることで
#     Spot → On-Demand など別ワーカーへジョブが自動リスケされる
#
#   env:
#     CHECKPOINT_DIR   … 永続ボリュームを指すパス (/mnt/checkpoints)
#     ONSPOT_INSTANCE  … "true" なら epoch 内で軽い sleep を入れて
#                         Kill シミュレーションがやりやすい（任意）
# =====================================================================
from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Tuple

import numpy as np
import pandas as pd
from pandas.tseries.offsets import BDay, CustomBusinessDay
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error

# ---------------------------------------------------------------------
# ロギング
# ---------------------------------------------------------------------
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# ---------------------------------------------------------------------
# 定数・環境変数
# ---------------------------------------------------------------------
TOTAL_EPOCHS = 12  # PoC: 1 epoch ≈ 5 s ×12 = およそ 1 min

CKPT_DIR = Path(os.getenv("CHECKPOINT_DIR", "/mnt/checkpoints")).expanduser()
CKPT_DIR.mkdir(parents=True, exist_ok=True)


def _ckpt_path(run_id: str) -> Path:
    """run_id → ckpt ファイルパス"""
    return CKPT_DIR / f"{run_id}.json"


# ---------------------------------------------------------------------
# データソースを抽象化（存在しなければ yfinance へフォールバック）
# ---------------------------------------------------------------------
try:
    from core.datasource import get_source

    _DATASOURCE = get_source()
except Exception:  # noqa: BLE001
    _DATASOURCE = None
    import yfinance as yf

    logger.warning("[Do] datasource fallback to yfinance because core.datasource is missing")


# =====================================================================
# 外部公開 API
# =====================================================================
def run_do(plan_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    1 回の Do-phase を実行し、JSON シリアライズ可能な dict を返す。

    必須 params
    ----------
    symbol : str
    start  : "YYYY-MM-DD"
    end    : "YYYY-MM-DD"
    run_no : int

    任意 params
    ----------
    indicators : list[{name, window}]
    holidays   : list["YYYY-MM-DD", …]
    """
    symbol, start, end, ind_cfg, run_no, holidays = _parse_params(params)
    run_id = f"{plan_id}__{run_no:04d}"

    # ---------- checkpoint 読み込み -------------------------------
    ckpt_fp = _ckpt_path(run_id)
    state: Dict[str, Any] = {"current_epoch": 0}
    if ckpt_fp.exists():
        try:
            state = json.loads(ckpt_fp.read_text())
            logger.info("[Do] resume run_id=%s  epoch=%d", run_id, state["current_epoch"])
        except json.JSONDecodeError:
            logger.warning("[Do] ckpt corrupted – 再学習します")

    logger.info(
        "[Do] ▶ run_id=%s  %s  %s→%s  epochs=%d-%d",
        run_id,
        symbol,
        start,
        end,
        state["current_epoch"],
        TOTAL_EPOCHS - 1,
    )

    # ---------- 価格取得 -----------------------------------------
    df = _download_prices(symbol, start, end)

    # ---------- インジケータ追加 ---------------------------------
    df = _add_indicators(df, ind_cfg)
    if len(df) < 30:
        raise RuntimeError("Not enough rows (≥ 30) after preprocessing")

    # ---------- 学習 & 予測 ---------------------------------------
    preds, model, feature_cols, metrics = _train_and_predict(df)

    # ---------- epoch loop（ダミー） ------------------------------
    #     * heavy な学習処理がある想定で各 epoch 5 s かかるポカヨケ
    #     * epoch 毎に ckpt commit → Spot 落ち時に再開可
    for epoch in range(state["current_epoch"], TOTAL_EPOCHS):
        _train_one_epoch(epoch)
        state["current_epoch"] = epoch + 1
        ckpt_fp.write_text(json.dumps(state))
        logger.debug("[Do] ckpt flush epoch=%d", epoch + 1)

    # ---------- 完了処理 -----------------------------------------
    ckpt_fp.unlink(missing_ok=True)  # 成功時は削除
    bday = _make_bday_offset(holidays)
    target_dates = (df.index + bday).strftime("%Y-%m-%d")

    last30 = [
        {"date": d, "price": float(round(p, 4))}
        for d, p in zip(target_dates[-30:], preds[-30:])
    ]

    summary = {
        "rows": int(len(df)),
        "features_used": feature_cols,
        "coef": np.round(model.coef_, 6).tolist(),
        "intercept": float(round(model.intercept_, 6)),
    }

    logger.info("[Do] ✓ run_id=%s DONE", run_id)

    return {
        "run_id": run_id,
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "summary": summary,
        "metrics": metrics,
        "predictions": last30,
    }


# =====================================================================
# internal helpers
# =====================================================================
def _train_one_epoch(epoch: int) -> None:
    """
    PoC 用のダミー学習。

    * 実環境では ML 学習や Backtest などを行う
    * ONSPOT_INSTANCE=true の場合は 5 s sleep で
      “途中で kill しやすい” ようにしてある
    """
    if os.getenv("ONSPOT_INSTANCE", "false").lower() == "true":
        time.sleep(5)
    else:
        time.sleep(0.5)  # 普通のワーカーは軽く


# ---------- params 解析 ----------
def _parse_params(
    params: Dict[str, Any],
) -> Tuple[str, str, str, List[Dict[str, Any]], int, List[str]]:
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

    holidays: List[str] = params.get("holidays", [])

    return symbol, start, end, indicators, run_no, holidays


def _make_bday_offset(holidays: List[str]):
    if holidays:
        return CustomBusinessDay(holidays=holidays)
    return BDay()


# ---------- price downloader ----------
def _download_prices(symbol: str, start: str, end: str) -> pd.DataFrame:
    if _DATASOURCE is not None:
        df = _DATASOURCE.fetch_ohlcv(symbol=symbol, start=start, end=end)
    else:
        df = yf.download(
            symbol,
            start=start,
            end=end,
            progress=False,
            auto_adjust=False,
            group_by="column",
        )

        # flatten MultiIndex
        if isinstance(df.columns, pd.MultiIndex):
            for level in (1, 0):  # try (field, ticker) then (ticker, field)
                try:
                    df = df.xs(symbol, level=level, axis=1, drop_level=True)
                    break
                except KeyError:
                    continue
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = ["_".join(map(str, c)) for c in df.columns]

        df.columns = [str(c).capitalize() for c in df.columns]
        if "Adj close" in df.columns:
            df = df.rename(columns={"Adj close": "Adj Close"})

    if df.empty:
        raise RuntimeError(f"No price data for '{symbol}'")

    required = ["Open", "High", "Low", "Close", "Volume"]
    if "Adj Close" in df.columns:
        required.insert(4, "Adj Close")

    missing = [c for c in required if c not in df.columns]
    if missing:
        raise RuntimeError(f"missing required columns: {missing}")

    return df[required].dropna(subset=["Close"]).copy()


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


_IND_FUNCS: Dict[str, Callable[[pd.Series, int], pd.Series]] = {
    "SMA": _sma,
    "EMA": _ema,
    "RSI": _rsi,
}


def _add_indicators(df: pd.DataFrame, cfg: List[Dict[str, Any]]) -> pd.DataFrame:
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

    if "SMA_5" not in df.columns:
        df["SMA_5"] = _sma(close, 5)

    return df.dropna()


def _train_and_predict(
    df: pd.DataFrame,
) -> Tuple[np.ndarray, LinearRegression, List[str], Dict[str, float]]:
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

    try:
        rmse = mean_squared_error(y, preds, squared=False)
    except TypeError:
        rmse = np.sqrt(mean_squared_error(y, preds))

    r2 = float(np.corrcoef(y, preds)[0, 1] ** 2)
    logger.info("[Do] rows=%d  r2=%.4f  rmse=%.4f", len(df), r2, rmse)

    return preds, model, feature_cols, {"r2": r2, "rmse": float(round(rmse, 6))}
