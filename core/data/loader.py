# =====================================================================
# ASSIST_KEY: 【core/data/loader.py】
# =====================================================================
#
# 【概要】
#   時系列データ（主に株価）を統一 I/O で取得するユーティリティ。
#   MVP では yfinance にフォールバックし、DataFrame を返す。
#
# 【主な役割】
#   - load(symbol, start, end, freq="1d") → pd.DataFrame
#   - 必要に応じてキャッシュ / リトライ / 列名正規化を実施
#
# 【連携先・依存関係】
#   - core/data/splitter.py : train/valid/test スプリットで利用
#   - core/feature/engineering.py : FE 前のデータソース
#
# 【ルール遵守】
#   1) 列は ["Date", "Open", "High", "Low", "Close", "Volume"] に統一
#   2) index=DatetimeIndex（UTC）で返す
#   3) ハードコード値には “TODO: 外部設定へ” コメント
# ---------------------------------------------------------------------

from __future__ import annotations

import logging
from datetime import datetime
from typing import Literal, Union

import pandas as pd

logger = logging.getLogger(__name__)

_FREQUENCY_MAP: dict[str, str] = {
    "1d": "1d",
    "1wk": "1wk",
    "1mo": "1mo",
}


def _try_import_yf():
    try:
        import yfinance as yf  # type: ignore
        return yf
    except ModuleNotFoundError as e:  # pragma: no cover
        msg = (
            "yfinance が見つかりません。`pip install yfinance` を実行してください。"
        )
        raise RuntimeError(msg) from e


def load(
    symbol: str,
    start: Union[str, datetime],
    end: Union[str, datetime],
    *,
    freq: Literal["1d", "1wk", "1mo"] = "1d",
    auto_adjust: bool = True,
) -> pd.DataFrame:
    """
    指定シンボルの時系列データを DataFrame で取得する。

    Parameters
    ----------
    symbol : str
        ティッカーシンボル（例: "AAPL"）
    start, end : str | datetime
        取得期間
    freq : {"1d","1wk","1mo"}, default "1d"
        ダウンサンプリング周期
    auto_adjust : bool, default True
        株式分割などを自動調整するか

    Returns
    -------
    pd.DataFrame
        DatetimeIndex（UTC）・標準列名の価格データ
    """
    yf = _try_import_yf()

    # --- yfinance download -------------------------------------------
    df = yf.download(
        symbol,
        start=start,
        end=end,
        interval=_FREQUENCY_MAP[freq],
        auto_adjust=auto_adjust,
        progress=False,
        threads=False,  # Windows でのマルチスレッド問題回避
    )

    if df.empty:
        raise ValueError(f"No data returned for {symbol}")

    # --- column rename -----------------------------------------------
    df = (
        df.rename(
            columns={
                "Open": "Open",
                "High": "High",
                "Low": "Low",
                "Close": "Close",
                "Adj Close": "Close",  # auto_adjust=False の場合
                "Volume": "Volume",
            }
        )
        .reset_index()
        .rename(columns={"Date": "Date"})
    )

    # --- enforce schema ----------------------------------------------
    keep_cols = ["Date", "Open", "High", "Low", "Close", "Volume"]
    df = df[keep_cols].copy()
    df["Date"] = pd.to_datetime(df["Date"], utc=True)
    df.set_index("Date", inplace=True)

    logger.info("[loader] fetched %d rows for %s", len(df), symbol)
    return df
