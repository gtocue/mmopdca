# =========================================================
# ASSIST_KEY: 【core/event_bus.py】
# =========================================================
#
# 【概要】
#   このユニットは EventBus として、
#   アプリ全域で発生するドメインイベントを *最小コスト* で publish する
#   『一時的スタブ (Null‑Object) 実装』を提供します。
#
# 【主な役割】
#   - `publish(event: dict)` を提供し、どの層からでも呼べる窓口を統一
#   - MVP フェーズでは **何もしない** (ログだけ残す) —> P1 以降で
#     ・Outbox テーブルへの INSERT
#     ・Redis Streams / Kafka への push
#     へ段階的に差し替えられる構造を担保
#
# 【連携先・依存関係】
#   - 他ユニット :
#       • core/do/..., core/check/..., core/act/... など publish 呼び出し元
#   - 外部設定 :
#       • ENV `EVENT_BUS_MODE=null|outbox|kafka` (TODO: 外部設定へ)
#       • .env で broker URL を後付け予定
#
# 【ルール遵守】
#   1) 追加のみ。publish() シグネチャは将来も維持する
#   2) 型安全: Pydantic BaseModel で EventEnvelope を定義
#   3) ログ以外の副作用は *今は持たない* (# NOTE 参照)
#   4) グローバル変数直書き禁止
#   5) TODO コメントで将来拡張ポイントを明示
#
# ---------------------------------------------------------
# NOTE:
#   • 現在は Null‑Object 実装だが、呼び出し側を増やすことで "イベント駆動化"
#     への移行コストをゼロに抑えるのが目的。
#   • publish() 内部で try/except し、例外を絶対に外へ漏らさない。
#     => 本番移行時でも "イベント送信失敗がビジネス処理を壊さない" という
#        アーキテクチャ特性を保持する。
# =========================================================
from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
if not logger.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("[%(levelname)s] %(name)s: %(message)s"))
    logger.addHandler(_h)
logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())


# ---------------------------------------------------------------------------
# Event Envelope Schema (stable API)
# ---------------------------------------------------------------------------
class EventEnvelope(BaseModel):
    """共通イベントラッパー (event sourcing 移行を見据えて固定化)。"""

    event_id: str = Field(..., description="UUIDv4 など一意ID")
    event_type: str = Field(..., description="ドメイン + 動詞 例: PLAN.APPROVED")
    occurred_at: datetime = Field(
        default_factory=datetime.utcnow, description="UTC now"
    )
    payload: dict[str, Any] = Field(default_factory=dict, description="Event body")
    version: int = Field(1, description="イベントスキーマバージョン")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
        frozen = True  # イミュータブル


# ---------------------------------------------------------------------------
# Runtime Mode 切替 (MVP = null)
# ---------------------------------------------------------------------------
_mode: Literal["null", "outbox", "kafka"] = os.getenv("EVENT_BUS_MODE", "null").lower()  # type: ignore

# TODO: P1 で Outbox 実装を追加する
# TODO: P2 で Kafka producer 実装を追加する


def publish(event: EventEnvelope | dict[str, Any]) -> None:  # noqa: D401
    """アプリ全域から呼ばれる単一インターフェース。

    *今は何もしない* が、呼び出し実績を作っておくことで
    後々のイベント駆動化を無摩擦にする。
    """

    try:
        envelope = EventEnvelope(**event) if isinstance(event, dict) else event
    except Exception as exc:  # noqa: BLE001
        logger.error("[EventBus] Invalid event format – %s", exc)
        return

    if _mode == "null":
        # # NOTE: 本番環境では debug ログが溢れないよう INFO 以上に絞る
        logger.debug("[EventBus] (noop) %s", envelope.json())
        return

    if _mode == "outbox":
        _publish_outbox(envelope)
    elif _mode == "kafka":
        _publish_kafka(envelope)
    else:  # pragma: no cover
        logger.warning("[EventBus] Unknown mode '%s' – fallback to noop", _mode)


# ---------------------------------------------------------------------------
# Internal back‑ends – MVP はダミー
# ---------------------------------------------------------------------------


def _publish_outbox(envelope: EventEnvelope) -> None:  # noqa: D401
    """P1 で Postgres outbox テーブルに INSERT 予定。"""
    # FIXME: 実装は後続フェーズ
    logger.info("[EventBus] (stub‑outbox) stored %s", envelope.event_type)


def _publish_kafka(envelope: EventEnvelope) -> None:  # noqa: D401
    """P2 で Kafka / Redpanda へ送信予定。"""
    # FIXME: 実装は後続フェーズ
    logger.info("[EventBus] (stub‑kafka) sent %s", envelope.event_type)


__all__ = [
    "EventEnvelope",
    "publish",
]
