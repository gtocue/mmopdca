# =========================================================
# ASSIST_KEY: 【utils/promsdk.py】
# =========================================================
# 
# 【概要】
#   Prometheus クエリ・ヘルパ SDK。
#   UI / API からメトリクスを単数・時系列で安全に取得します。
# 
# 【主な役割】
#   - Prometheus HTTP API v1/query, v1/query_range 呼び出し
#   - 30 秒 TTL キャッシュによる負荷削減
#   - 例外 → 専用エラー型 (PromQueryError) 変換
# 
# 【連携先・依存関係】
#   - api/routers/metrics.py : /metrics/ ルータが本 SDK を直接利用
#   - metrics/signal_catalog.yml : expr 定義を外部化し、SDK で評価
# 
# 【ルール遵守】
#   1) グローバル直書き禁止。環境変数 → pdca_data or os.getenv 経由
#   2) タイムアウトは 2 秒。可観測性重視で logging
#   3) 全体コード返却（完成形）。このヘッダーは残す
# 
# ---------------------------------------------------------

from __future__ import annotations

import json
import logging
import os
import time
from typing import Dict, Literal, Sequence

import cachetools
import httpx

__all__ = [
    "PromQueryError",
    "PromSDK",
]

# ────────────────────────────────
# ロガー
# ────────────────────────────────
logger = logging.getLogger(__name__)
if not logger.handlers:  # 多重登録防止
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("[%(levelname)s] %(name)s: %(message)s"))
    logger.addHandler(_h)
logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())

# ────────────────────────────────
# 型定義
# ────────────────────────────────

class PromQueryError(RuntimeError):
    """Prometheus からのエラー応答 / ネットワーク障害を統一的に表現"""

    def __init__(self, expr: str, detail: str):
        super().__init__(f"Prometheus query failed: {expr} – {detail}")
        self.expr = expr
        self.detail = detail


RangeStep = Literal["5s", "10s", "15s", "30s", "1m", "5m"]

# ────────────────────────────────
# Prom SDK 本体
# ────────────────────────────────


class PromSDK:
    """Prometheus HTTP API v1 wrapper.

    NOTE: ベーシックな *instant* / *range* クエリのみ実装。
    複雑な series/select は UI 側ユースケース外のため対象外。
    """

    _CACHE_TTL = 30  # 秒 TODO: 外部設定へ

    def __init__(self, base_url: str | None = None):
        self.base_url = base_url or os.getenv("PROM_URL", "http://prom:9090")
        self._session = httpx.Client(base_url=self.base_url, timeout=2.0)
        self._cache: cachetools.TTLCache[str, float] = cachetools.TTLCache(
            maxsize=256, ttl=self._CACHE_TTL
        )

    # --------------------------------------------------
    # public
    # --------------------------------------------------
    def instant(self, expr: str) -> float:
        """単一値を取得。30 秒キャッシュ有り。"""
        if expr in self._cache:
            return self._cache[expr]
        result = self._fetch("/api/v1/query", {"query": expr})
        value = float(result[0]["value"][1])  # [timestamp, value]
        self._cache[expr] = value
        return value

    def range(
        self,
        expr: str,
        start_unix: int,
        end_unix: int,
        step: RangeStep = "30s",
    ) -> Sequence[tuple[int, float]]:
        """範囲クエリ (折れ線チャート用)。キャッシュしない。"""
        params = {
            "query": expr,
            "start": str(start_unix),
            "end": str(end_unix),
            "step": step,
        }
        result = self._fetch("/api/v1/query_range", params)
        # result = {"metric": {...}, "values": [[ts, val], ...]}
        return [(int(ts), float(val)) for ts, val in result[0]["values"]]

    # --------------------------------------------------
    # private helpers
    # --------------------------------------------------
    def _fetch(self, path: str, params: Dict[str, str]) -> list[dict[str, object]]:
        url = f"{self.base_url.rstrip('/')}{path}"
        try:
            r = self._session.get(url, params=params)
            r.raise_for_status()
            payload = r.json()
            if payload["status"] != "success":
                raise PromQueryError(params.get("query", "-"), json.dumps(payload))
            return payload["data"]["result"]  # type: ignore[index]
        except (httpx.HTTPError, KeyError, ValueError) as exc:  # noqa: PERF203
            logger.error("[PromSDK] %s", exc)
            raise PromQueryError(params.get("query", "-"), str(exc)) from exc

    # --------------------------------------------------
    # teardown
    # --------------------------------------------------
    def close(self) -> None:
        """明示的に HTTP セッションを閉じる (テスト用)"""
        self._session.close()
        self._cache.clear()


# NOTE: アプリ全体で 1 インスタンス使い回し (モジュールシングルトン)
_prom = PromSDK()

# 外部に薄い関数型 API をも提供
instant_query = _prom.instant
range_query = _prom.range
