# =========================================================
# core/datasource/premium_source.py
# =========================================================
#
# PremiumDataSource ― 将来の有料プロバイダ用プレースホルダ
#   * SDK/REST クライアントは未定のため TODO で stub 実装
#   * 本番導入時はここを書き換えるだけで executor 側は無改修
# ---------------------------------------------------------
from __future__ import annotations

import logging
from typing import Final

import pandas as pd

from .contract import IDataSource

logger = logging.getLogger(__name__)
__all__: Final = ["PremiumDataSource"]


class PremiumDataSource(IDataSource):
    """
    TODO: 高級データソース SDK に置き換える

    * fetch_ohlcv() が IDataSource 契約を満たすように実装する
    * 認証トークン／レート制限リトライはこのクラス内で完結させる
    """

    def __init__(self) -> None:
        # FIXME: ハードコード － 認証情報は env / secrets に逃がすこと
        self.api_key: str | None = None

    # -----------------------------------------------------
    # IDataSource
    # -----------------------------------------------------
    def fetch_ohlcv(
        self, *, symbol: str, start: str, end: str
    ) -> pd.DataFrame:  # noqa: D401
        raise NotImplementedError(
            "PremiumDataSource is a stub. Implement SDK call here."
        )
