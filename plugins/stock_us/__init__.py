"""
US 株プラグイン – pandas-datareader / yfinance を包む簡易 adapter
呼び出し側: repo = get_adapter("stock_us")
"""
from __future__ import annotations
import logging
from datetime import date
import yfinance as yf

logger = logging.getLogger(__name__)

class StockUSAdapter:
    """株価取得のシンプル実装（終値のみ）"""

    def fetch_prices(self, symbol: str, start: date, end: date):
        logger.info("Fetch %s price from %s to %s", symbol, start, end)
        df = yf.download(symbol, start=start, end=end, progress=False)
        return (
            df[["Close"]]
            .rename(columns={"Close": "close"})
            .reset_index()
            .to_dict(orient="records")
        )

# --- 登録処理 (インポート時に 1 度だけ呼ばれる) -----------------------
from core.adapters.registry import register  # 適宜パスを合わせて下さい
register("stock_us", StockUSAdapter())
