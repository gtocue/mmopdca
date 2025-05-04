import yfinance as yf
import pandas as pd
from datetime import datetime

class StockUSAdapter(BaseAdapter):
    # …load/plan は後回し …

    def do(self, plan: dict) -> dict:
        symbol = plan["symbol"]
        start  = plan["start"]
        end    = plan["end"]

        df = yf.download(symbol, start=start, end=end, progress=False)

        sma_window = plan["indicators"][0]["window"]
        df["SMA"] = df["Close"].rolling(sma_window).mean()

        latest = df.iloc[-1]
        return {
            "symbol": symbol,
            "as_of": datetime.utcnow().isoformat(),
            "close": float(latest["Close"]),
            "sma":   float(latest["SMA"]),
        }
