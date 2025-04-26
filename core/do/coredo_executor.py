# ASSIST_KEY: このファイルは【core/do/coredo_executor.py】に位置するユニットです.
#
# 【概要】
#   Do フェーズ実行エンジン (CoreDoExecutor)。
#   Plan で決定した銘柄・期間・指標を用い、データ取得 → 特徴量生成 →
#   簡易モデル推論までを行う MVP 実装。
#
# 【主な役割】
#   - run_do()            : 外向け API。Plan パラメータで実行し結果 dict を返す
#   - _download_prices()  : yfinance で株価ロー・ハイ・終値など取得
#   - _add_indicators()   : SMA 等の基本指標を Pandas で付与
#
# 【連携先・依存関係】
#   - 他ユニット : core/schemas/do_schemas.DoCreateRequest
#   - 外部設定   : なし（将来 settings.yaml へ切り出し予定）
#
# 【ルール遵守】
#   1) メイン銘柄 "Close_main", "Open_main" は直接扱わない
#   2) 市場は "Close_Nikkei_225", "Open_Nikkei_225" の suffix を使う
#   3) コード返却は全体コードで行う
#   4) ファイル先頭に本ファイル名を記載する
#   5) 機能削除は事前相談（今回は追加のみ）
#   6) pdca_data[...] に統一する（本ユニットは pdca_data を直接扱わない）
#
# 【注意事項】
#   - ハードコード多数 → “MVP デモ” 用。実運用では DI & 設定化してください
# ---------------------------------------------------------

from __future__ import annotations

import logging
from typing import Any, Dict, List

import pandas as pd
import yfinance as yf
from sklearn.linear_model import LinearRegression

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


# ======================================================================
# Public API
# ======================================================================
def run_do(plan_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Plan パラメータを受け取り、単一銘柄の簡易モデルで予測を行う。

    Parameters
    ----------
    plan_id : str
        紐付く Plan の ID（ログ用）
    params : dict
        DoCreateRequest の内容 (symbol, start, end, indicators ...)

    Returns
    -------
    dict
        {
            "summary": {...},
            "predictions": [...],
            "metrics": {...}
        }
    """
    symbol: str = params["symbol"]
    start: str = params["start"]
    end: str = params["end"]
    indicators: List[Dict[str, Any]] = params.get("indicators", [])

    logger.info("[Do] ▸ plan_id=%s  symbol=%s  %s→%s", plan_id, symbol, start, end)

    # -- データ取得 & 前処理 ------------------------------------------------
    df = _download_prices(symbol, start, end)
    df = _add_indicators(df, indicators)

    # -- 超簡易モデル：5 日 SMA → 翌日終値を線形回帰 -------------------------
    if len(df) < 30:
        raise RuntimeError("Not enough price data (≥30 rows required)")

    df["target"] = df["Close"].shift(-1)
    df = df.dropna()

    X = df[["SMA_5"]]
    y = df["target"]

    model = LinearRegression()
    model.fit(X, y)
    preds = model.predict(X)

    logger.info("[Do] ✓ completed rows=%d  r2=%.4f", len(df), model.score(X, y))

    return {
        "summary": {
            "rows": len(df),
            "coef": float(model.coef_[0]),
            "intercept": float(model.intercept_),
        },
        "predictions": [float(p) for p in preds[:30]],  # 先頭 30 件だけ返す
        "metrics": {
            "r2": float(model.score(X, y)),
        },
    }


# ======================================================================
# Internal helpers
# ======================================================================
def _download_prices(symbol: str, start: str, end: str) -> pd.DataFrame:
    """yfinance で OHLCV を取得"""
    df = yf.download(symbol, start=start, end=end, progress=False)
    if df.empty:
        raise RuntimeError(f"No price data for '{symbol}'")
    return df


def _add_indicators(df: pd.DataFrame, indicators: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    指定されたインジケータを DataFrame に付与。
    現状は SMA のみ対応。
    """
    for ind in indicators:
        if ind["name"].upper() == "SMA":
            win = int(ind.get("window", 5))
            col = f"SMA_{win}"
            if col not in df.columns:
                df[col] = df["Close"].rolling(win).mean()

    # モデルで必須の 5 日 SMA が無ければ自動で付与
    if "SMA_5" not in df.columns:
        df["SMA_5"] = df["Close"].rolling(5).mean()

    return df
