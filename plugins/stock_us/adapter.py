# plugins/stock_us/adapter.py
import yfinance as yf
from datetime import datetime
from core.adapters.base import BaseAdapter  # 適切な import パスに置き換えてください


class StockUSAdapter(BaseAdapter):
    # …load/plan は後回し …

    def do(self, plan: dict) -> dict:
        symbol = plan["symbol"]
        start = plan["start"]
        end = plan["end"]

        df = yf.download(symbol, start=start, end=end, progress=False)

        sma_window = plan["indicators"][0]["window"]
        df["SMA"] = df["Close"].rolling(sma_window).mean()

        latest = df.iloc[-1]
        return {
            "symbol": symbol,
            "as_of": datetime.utcnow().isoformat(),
            "close": float(latest["Close"]),
            "sma": float(latest["SMA"]),
        }
