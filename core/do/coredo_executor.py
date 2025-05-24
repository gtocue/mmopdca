# ======================================================================
# core/do/coredo_executor.py   (2025-05-25 – Pylance clean build)
# ======================================================================

from __future__ import annotations

import logging
import os
import time
from datetime import datetime, timezone
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Sequence,
    Tuple,
    TYPE_CHECKING,
    cast,
)

# ----------------------------------------------------------------------
# ── Scientific stack: import が無くても動く様に “弱依存” 化
# ----------------------------------------------------------------------
if TYPE_CHECKING:  # 型チェック専用
    import numpy  # type: ignore
    import pandas  # type: ignore
    from sklearn.linear_model import LinearRegression  # type: ignore
    from pandas.tseries.offsets import BaseOffset

try:
    import numpy as _np  # noqa: N811
    import pandas as _pd  # noqa: N811
    from pandas.tseries.offsets import (
        BDay as _BDay,
        CustomBusinessDay as _CBD,
        BaseOffset as _BaseOffset,
    )  # noqa: N811
    from sklearn.linear_model import LinearRegression as _LinReg  # noqa: N811
    from sklearn.metrics import mean_squared_error as _mse  # noqa: N811
except Exception:  # pragma: no cover – headless CI を許可
    _np = _pd = _LinReg = _mse = None  # type: ignore
    _BDay = _CBD = _BaseOffset = object  # type: ignore

# ----------------------------------------------------------------------
# ── Project helpers
# ----------------------------------------------------------------------
from core.do import checkpoint as ckpt
from core.common.io_utils import save_predictions
from core.constants import ensure_directories

# ----------------------------------------------------------------------
# ── Logger
# ----------------------------------------------------------------------
logger = logging.getLogger(__name__)
if not logger.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("[%(levelname)s] %(name)s: %(message)s"))
    logger.addHandler(_h)
logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())

# ----------------------------------------------------------------------
# ── Env & Const
# ----------------------------------------------------------------------
TOTAL_EPOCHS: int = int(os.getenv("DO_TOTAL_SHARDS", "12"))
METRIC_THRESHOLD: float = float(os.getenv("CHECK_R2_THRESHOLD", "0.80"))

# ----------------------------------------------------------------------
# ── Data-source (primary → fallback → none)
# ----------------------------------------------------------------------
try:
    from core.datasource import get_source  # type: ignore

    _DS = get_source()
except Exception:  # noqa: BLE001
    _DS = None
    try:
        import yfinance as yf  # type: ignore

        logger.warning("[Do] datasource fallback to yfinance")
    except Exception:  # pragma: no cover
        yf = None  # type: ignore
        logger.warning("[Do] datasource fallback disabled (no yfinance)")

# ======================================================================
# Public API
# ======================================================================
def run_do(  # noqa: C901 – acceptable for MVP
    plan_id: str,
    params: Dict[str, Any],
    *,
    epoch_idx: int = 0,
    epoch_cnt: int = TOTAL_EPOCHS,
) -> Dict[str, Any]:
    """
    Execute **one shard** (epoch).  
    ├─ last shard  : returns metrics / predictions / artifact URI  
    └─ other shard : lightweight progress payload
    """
    ensure_directories()

    sym, start, end, ind_cfg, run_no, holidays = _parse_params(params)
    run_id = f"{plan_id}__{run_no:04d}"

    # ── headless CI: dependencies missing → stub response
    if _pd is None or _np is None:  # pragma: no cover
        return {
            "run_id": run_id,
            "epoch": epoch_idx + 1,
            "status": "IN_PROGRESS",
            "skipped": True,
        }

    # ── duplicate guard
    if ckpt.is_done(run_id, epoch_idx):
        return {"run_id": run_id, "epoch": epoch_idx, "status": "SKIPPED_DUPLICATE"}

    # ── resume & dummy training
    state = ckpt.load_latest_ckpt(run_id, epoch_idx) or {"current_epoch": 0}
    _sleep_training(epoch_idx)
    state["current_epoch"] = epoch_idx + 1
    ckpt.save_ckpt(run_id, epoch_idx, state)

    # ── final shard
    if epoch_idx + 1 == epoch_cnt:
        df = _download_prices(sym, start, end)
        df = _add_indicators(df, ind_cfg)
        preds, model, feats, raw_m = _train_and_predict(df)

        ckpt.mark_done(run_id, epoch_idx)

        # 30 business-day ahead forecast
        bday: _BaseOffset = _make_bday_offset(holidays)  # type: ignore[assignment]
        fut_dates = (
            cast("pandas.DatetimeIndex", df.index) + bday  # type: ignore[operator]
        ).strftime("%Y-%m-%d")[-30:]
        last30 = [
            {"date": d, "price": float(round(p, 4))}
            for d, p in zip(fut_dates, preds[-30:])
        ]

        uri = _save_prediction_artifact(df, preds, plan_id, run_id)
        r2_val = raw_m["r2"]

        return {
            "status": "SUCCESS",
            "run_id": run_id,
            "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "summary": {
                "rows": int(len(df)),
                "features_used": feats,
                "coef": _np.round(model.coef_, 6).tolist(),  # type: ignore[arg-type]
                "intercept": float(round(float(model.intercept_), 6)),
            },
            "metrics": {
                **raw_m,
                "threshold": METRIC_THRESHOLD,
                "passed": bool(r2_val >= METRIC_THRESHOLD),
            },
            "predictions": last30,
            "artifact_uri": uri,
        }

    # ── intermediate shard
    return {"run_id": run_id, "epoch": epoch_idx + 1, "status": "IN_PROGRESS"}

# ======================================================================
# Helpers
# ======================================================================
def _sleep_training(epoch: int) -> None:
    """simulate GPU workload"""
    time.sleep(5 if os.getenv("ONSPOT_INSTANCE", "false").lower() == "true" else 0.5)


def _parse_params(
    params: Dict[str, Any],
) -> Tuple[str, str, str, List[Dict[str, Any]], int, List[str]]:
    def _rq(key: str) -> Any:
        if key not in params:
            raise RuntimeError(f"missing param '{key}'")
        return params[key]

    sym: str = str(_rq("symbol"))
    start: str = str(_rq("start"))
    end: str = str(_rq("end"))
    run_no: int = int(_rq("run_no"))
    ind_cfg: List[Dict[str, Any]] = cast(
        List[Dict[str, Any]], params.get("indicators") or [{"name": "SMA", "window": 5}]
    )
    hol: List[str] = cast(List[str], params.get("holidays", []))
    return sym, start, end, ind_cfg, run_no, hol


def _make_bday_offset(holidays: List[str]):
    """Return pandas offset; stub signature in stubs → ignore type."""
    return _CBD(holidays=holidays) if holidays else _BDay()  # type: ignore[arg-type]


# ------------------------------ data fetch ----------------------------
def _download_prices(symbol: str, start: str, end: str):  # -> pandas.DataFrame
    if _DS is not None:
        df = _DS.fetch_ohlcv(symbol=symbol, start=start, end=end)
    elif "yf" in globals() and yf is not None:
        df = yf.download(  # type: ignore[attr-defined]
            symbol, start=start, end=end, progress=False, auto_adjust=False, group_by="column"
        )
    else:
        raise RuntimeError("no datasource available")

    if df.empty:  # type: ignore[attr-defined]
        raise RuntimeError("no price data")

    if isinstance(df.columns, _pd.MultiIndex):  # type: ignore[attr-defined]
        df.columns = ["_".join(map(str, c)) for c in df.columns]  # type: ignore[attr-defined]
    df.columns = [str(c).capitalize() for c in df.columns]  # type: ignore[attr-defined]

    req: Sequence[str] = ["Open", "High", "Low", "Close", "Volume"]
    if "Adj close" in df.columns:  # type: ignore[attr-defined]
        df = df.rename(columns={"Adj close": "Adj Close"})  # type: ignore[attr-defined]
        req = [*req[:4], "Adj Close", "Volume"]

    missing = [c for c in req if c not in df.columns]  # type: ignore[attr-defined]
    if missing:
        raise RuntimeError(f"missing columns {missing}")

    return df[req].dropna(subset=["Close"]).copy()  # type: ignore[attr-defined]


# ------------------------------ indicators ---------------------------
def _sma(s: "pandas.Series", w: int) -> "pandas.Series":
    return s.rolling(w, min_periods=w).mean()


def _ema(s: "pandas.Series", w: int) -> "pandas.Series":
    return s.ewm(span=w, adjust=False).mean()


def _rsi(s: "pandas.Series", w: int) -> "pandas.Series":
    delta = s.diff()
    gain = delta.clip(lower=0).rolling(w, min_periods=w).mean()
    loss = -delta.clip(upper=0).rolling(w, min_periods=w).mean()
    rs = gain / loss.replace(0, 1e-9)
    return 100 - (100 / (1 + rs))


_IND_FUNCS: Dict[str, Callable[["pandas.Series", int], "pandas.Series"]] = {
    "SMA": _sma,
    "EMA": _ema,
    "RSI": _rsi,
}


def _add_indicators(df: "pandas.DataFrame", cfg: List[Dict[str, Any]]) -> "pandas.DataFrame":
    close = df["Close"]
    for ind in cfg:
        name = str(ind["name"]).upper()
        win = int(ind.get("window", 5))
        col = f"{name}_{win}"
        func = _IND_FUNCS.get(name)
        if func is None:
            raise RuntimeError(f"unsupported indicator '{name}'")
        if col not in df.columns:
            df[col] = func(close, win)

    if "SMA_5" not in df.columns:
        df["SMA_5"] = _sma(close, 5)
    return df.dropna()


# ------------------------------ model --------------------------------
def _train_and_predict(
    df: "pandas.DataFrame",
) -> Tuple[
    "numpy.ndarray",
    "LinearRegression",
    List[str],
    Dict[str, float],
]:
    df = df.assign(target=df["Close"].shift(-1)).dropna()
    feats: List[str] = [c for c in df.columns if c.startswith(("SMA_", "EMA_", "RSI_"))]
    if not feats:
        raise RuntimeError("no features")

    X = cast("numpy.ndarray", df[feats].values)
    y = cast("numpy.ndarray", df["target"].values)
    model: "LinearRegression" = _LinReg().fit(X, y)  # type: ignore
    preds = model.predict(X)

    rmse_val = float(_mse(y, preds, squared=False))  # type: ignore
    r2_val = float(_np.corrcoef(y, preds)[0, 1] ** 2)  # type: ignore
    logger.info("[Do] rows=%d r2=%.4f rmse=%.4f", len(df), r2_val, rmse_val)

    return preds, model, feats, {"r2": r2_val, "rmse": rmse_val}


# ------------------------------ artifact -----------------------------
def _save_prediction_artifact(
    df: "pandas.DataFrame",
    preds: "numpy.ndarray",
    plan_id: str,
    run_id: str,
) -> str:
    art_df = _pd.DataFrame(  # type: ignore[attr-defined]
        {
            "symbol": plan_id,
            "ts": df.index,
            "horizon": 1,
            "y_true": df["Close"].shift(-1).dropna(),
            "y_pred": preds,
            "model_id": "linreg",
        }
    ).dropna()

    return save_predictions(art_df, plan_id=plan_id, run_id=run_id)
