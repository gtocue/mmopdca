# =========================================================
# core/datasource/__init__.py
# =========================================================
#
# データソース・ファクトリ
#   get_source() で環境変数 / 引数に応じた IDataSource 実装を返す。
#   デフォルトは 'yahoo'。
# ---------------------------------------------------------
from __future__ import annotations

import os
from typing import Final

from .contract import IDataSource
from .yahoo_source import YahooFinanceSource
from .premium_source import PremiumDataSource

__all__: Final = ["get_source"]


def get_source(name: str | None = None) -> IDataSource:
    """
    Parameters
    ----------
    name : {'yahoo','premium'} | None
        None の場合は ENV `DATA_SOURCE` → 'yahoo' の順で決定。

    Returns
    -------
    IDataSource
    """
    name = (name or os.getenv("DATA_SOURCE") or "yahoo").lower()

    if name == "yahoo":
        return YahooFinanceSource()
    if name == "premium":
        return PremiumDataSource()

    raise ValueError(f"Unknown DATA_SOURCE '{name}'")
