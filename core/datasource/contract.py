# =========================================================
# core/datasource/contract.py
# =========================================================
#
# IDataSource ― OHLCV を提供する **データソース契約 (インターフェース)**
#   * fetch_ohlcv() のシグネチャを定義するだけ
# ---------------------------------------------------------
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Final

import pandas as pd

__all__: Final = ["IDataSource"]


class IDataSource(ABC):
    """外部データソースの取得インターフェース"""

    @abstractmethod
    def fetch_ohlcv(
        self, *, symbol: str, start: str, end: str
    ) -> pd.DataFrame:  # noqa: D401
        """
        Parameters
        ----------
        symbol : str
            ティッカー
        start, end : str
            ISO 日付 (YYYY-MM-DD)

        Returns
        -------
        pd.DataFrame
            必須列: Open / High / Low / Close / Adj Close / Volume
        """
        raise NotImplementedError
