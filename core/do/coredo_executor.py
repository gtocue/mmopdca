# ======================================================================
#  core/do/coredo_executor.py
# ======================================================================
#
# Do-phase Executor  ― Spot-Checkpoint × Shard 拡張版
#
# 1. 価格データ取得      (IDataSource → fallback: yfinance)
# 2. テクニカル指標計算  SMA / EMA / RSI
# 3. 線形回帰で翌営業日 Close を予測
# 4. shard(epoch) 毎にチェックポイント保存して再開保証
#
# Check-phase へ返すインターフェース
#   └ 最終 shard の return に **status / r2 / threshold / passed** を含める
# ----------------------------------------------------------------------

from __future__ import annotations

import logging
import os
import time
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Sequence, Tuple

import numpy as np
import pandas as pd
from pandas.tseries.offsets import BDay, CustomBusinessDay
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error

from core.do import checkpoint as ckpt
from core.common.io_utils import save_predictions
from core.constants import ensure_directories

# ───────────────────────────── logger
logger = logging.getLogger(__name__)
if not logger.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("[%(levelname)s] %(name)s: %(message)s"))
    logger.addHandler(_h)
logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())

# ───────────────────────────── env & const
TOTAL_EPOCHS: int   = int(os.getenv("DO_TOTAL_SHARDS", "12"))
METRIC_THRESHOLD: float = float(os.getenv("CHECK_R2_THRESHOLD", "0.80"))

# ───────────────────────────── datasource
try:
    from core.datasource import get_source  # type: ignore

    _DS = get_source()
except Exception:  # noqa: BLE001
    _DS = None
    import yfinance as yf  # type: ignore

    logger.warning("[Do] datasource fallback to yfinance")

# ======================================================================
# public API
# ======================================================================
def run_do(
    plan_id: str,
    params: Dict[str, Any],
    *,
    epoch_idx: int = 0,
    epoch_cnt: int = TOTAL_EPOCHS,
) -> Dict[str, Any]:
    """
    1 shard (=1 epoch) 分の処理を行う。

    * 最終 shard は詳細結果 (summary / metrics / predictions …) を返す
    * 中間 shard は軽量オブジェクトのみ返す
    """
    ensure_directories()  # artifacts/・pdca_data/ を必ず作成

    sym, start, end, ind_cfg, run_no, holidays = _parse_params(params)
    run_id = f"{plan_id}__{run_no:04d}"

    # ───── duplicate guard
    if ckpt.is_done(run_id, epoch_idx):
        logger.info("[Do] duplicate – %s epoch %d already done", run_id, epoch_idx)
        return {"run_id": run_id, "epoch": epoch_idx, "status": "SKIPPED_DUPLICATE"}

    # ───── checkpoint resume
    state = ckpt.load_latest_ckpt(run_id, epoch_idx) or {"current_epoch": 0}
    logger.info(
        "[Do] run %s epoch %d/%d (resume=%s)",
        run_id,
        epoch_idx,
        epoch_cnt,
        state["current_epoch"],
    )

    # ───── simulate training work & flush ckpt
    _train_one_epoch(epoch_idx)
    state["current_epoch"] = epoch_idx + 1
    ckpt.save_ckpt(run_id, epoch_idx, state)

    # ───── 最終 shard でフルパイプライン
    if epoch_idx + 1 == epoch_cnt:
        df = _download_prices(sym, start, end)
        df = _add_indicators(df, ind_cfg)
        preds, model, fcols, m = _train_and_predict(df)

        # checkpoint 完了マーク
        ckpt.mark_done(run_id, epoch_idx)

        # 直近 30 business-day 予測
        bday = _make_bday_offset(holidays)
        dates = (df.index + bday).strftime("%Y-%m-%d")[-30:]
        last30 = [{"date": d, "price": float(round(p, 4))} for d, p in zip(dates, preds[-30:])]

        # Parquet artifact
        artifact_uri = _save_prediction_artifact(df, preds, plan_id, run_id)

        # ---- Check-phase が必要とするフィールド
        r2 = m["r2"]
        passed = bool(r2 >= METRIC_THRESHOLD)
        metrics = {
            "r2": r2,
            "rmse": m["rmse"],
            "threshold": METRIC_THRESHOLD,
            "passed": passed,
        }

        return {
            "status": "SUCCESS",          # ★ Check が参照
            "run_id": run_id,
            "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "summary": {
                "rows": int(len(df)),
                "features_used": fcols,
                "coef": np.round(model.coef_, 6).tolist(),
                "intercept": float(round(model.intercept_, 6)),
            },
            "metrics": metrics,
            "predictions": last30,
            "artifact_uri": artifact_uri,
        }

    # ───── intermediate shard
    return {"run_id": run_id, "epoch": epoch_idx + 1, "status": "IN_PROGRESS"}


# ======================================================================
# internal helpers
# ======================================================================
def _train_one_epoch(epoch: int) -> None:
    """疑似的な学習時間を sleep で再現。"""
    if os.getenv("ONSPOT_INSTANCE", "false").lower() == "true":
        time.sleep(5)
    else:
        time.sleep(0.5)


def _parse_params(params: Dict[str, Any]) -> Tuple[str, str, str, List[Dict[str, Any]], int, List[str]]:
    def _req(k: str) -> Any:
        if k not in params:
            raise RuntimeError(f"missing param '{k}'")
        return params[k]

    sym = str(_req("symbol"))
    start = str(_req("start"))
    end = str(_req("end"))
    run_no = int(_req("run_no"))
    ind = params.get("indicators") or [{"name": "SMA", "window": 5}]
    if not isinstance(ind, list):
        raise RuntimeError("indicators must be list[dict]")
    hol = params.get("holidays", [])
    return sym, start, end, ind, run_no, hol


def _make_bday_offset(holidays: List[str]):
    return CustomBusinessDay(holidays=holidays) if holidays else BDay()


def _download_prices(symbol: str, start: str, end: str) -> pd.DataFrame:
    if _DS is not None:
        df = _DS.fetch_ohlcv(symbol=symbol, start=start, end=end)
    else:
        df = yf.download(  # type: ignore
            symbol, start=start, end=end, progress=False, auto_adjust=False, group_by="column"
        )

    if df.empty:
        raise RuntimeError("no price data")

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = ["_".join(map(str, c)) for c in df.columns]
    df.columns = [str(c).capitalize() for c in df.columns]

    req: Sequence[str] = ["Open", "High", "Low", "Close", "Volume"]
    if "Adj close" in df.columns:
        df = df.rename(columns={"Adj close": "Adj Close"})
        req = list(req); req.insert(4, "Adj Close")

    miss = [c for c in req if c not in df.columns]
    if miss:
        raise RuntimeError(f"missing columns {miss}")
    return df[req].dropna(subset=["Close"]).copy()


def _sma(s: pd.Series, w: int) -> pd.Series:
    return s.rolling(w, min_periods=w).mean()


def _ema(s: pd.Series, w: int) -> pd.Series:
    return s.ewm(span=w, adjust=False).mean()


def _rsi(s: pd.Series, w: int) -> pd.Series:
    delta = s.diff()
    gain = delta.clip(lower=0).rolling(w, min_periods=w).mean()
    loss = -delta.clip(upper=0).rolling(w, min_periods=w).mean()
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
            raise RuntimeError(f"unsupported indicator '{name}'")
        if col not in df.columns:
            df[col] = func(close, win)

    # デフォルトで SMA_5 を必ず入れる
    if "SMA_5" not in df.columns:
        df["SMA_5"] = _sma(close, 5)
    return df.dropna()


def _train_and_predict(
    df: pd.DataFrame,
) -> Tuple[np.ndarray, LinearRegression, List[str], Dict[str, float]]:
    df = df.assign(target=df["Close"].shift(-1)).dropna()
    feats = [c for c in df.columns if c.startswith(("SMA_", "EMA_", "RSI_"))]
    if not feats:
        raise RuntimeError("no features")

    X, y = df[feats].values, df["target"].values
    model = LinearRegression().fit(X, y)
    preds = model.predict(X)

    rmse = mean_squared_error(y, preds, squared=False)
    r2 = float(np.corrcoef(y, preds)[0, 1] ** 2)
    logger.info("[Do] rows=%d r2=%.4f rmse=%.4f", len(df), r2, rmse)

    return preds, model, feats, {"r2": r2, "rmse": float(round(rmse, 6))}


# --------------------------------------------------
# prediction artifact helper
# --------------------------------------------------
def _save_prediction_artifact(
    df: pd.DataFrame,
    preds: np.ndarray,
    plan_id: str,
    run_id: str,
) -> str:
    """df + preds → Parquet を生成して保存 URI を返す。"""
    artifact_df = pd.DataFrame(
        {
            "symbol": df.index.map(lambda _: plan_id),  # TODO: symbol カラム追加予定
            "ts": df.index,
            "horizon": 1,
            "y_true": df["Close"].shift(-1).dropna(),
            "y_pred": preds,
            "model_id": "linreg",
        }
    ).dropna()

    return save_predictions(artifact_df, plan_id=plan_id, run_id=run_id)
