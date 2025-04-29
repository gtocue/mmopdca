# =========================================================
# ASSIST_KEY: 【core/celery_app.py】
# =========================================================
#
# 【概要】
#   Celery ワーカー／ビート共通の “アプリケーション本体” を定義します。
#   - `celery_app` を公開するだけの薄いラッパーモジュール
#
# 【主な役割】
#   - ブローカー & リザルトバックエンド URL の読み込み（.env / 環境変数）
#   - ベーシックなシリアライザ設定・タイムゾーン設定
#   - 主要タスク（run_do 等）の登録
#
# 【連携先・依存関係】
#   - core.do.coredo_executor.run_do  … 価格取得＋予測の実体
#   - docker-compose.yml             … worker/beat から `-A core.celery_app:celery_app`
#
# 【ルール遵守】
#   1) グローバル変数直書きは避け、環境変数経由で注入
#   2) 機能追加のみ可（破壊的変更 NG）
#   3) 型ヒント・ログを必ず付与
#   4) TODO/NOTE/FIXME による改善提案を歓迎
#
# ---------------------------------------------------------

from __future__ import annotations

import logging
import os
from typing import Any, Dict

from celery import Celery

# ----------------------------------------------------------------------
# ロギング
# ----------------------------------------------------------------------
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# ----------------------------------------------------------------------
# ブローカー / バックエンド URL を環境変数から取得
#   ※ docker-compose.yml で .env を渡す前提
# ----------------------------------------------------------------------
BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
RESULT_BACKEND_URL: str = os.getenv("CELERY_RESULT_BACKEND", BROKER_URL)

logger.info(
    "[Celery] init  broker_url=%s  backend=%s",
    BROKER_URL,
    RESULT_BACKEND_URL,
)

# ----------------------------------------------------------------------
# Celery インスタンス生成
#   - アプリ名はパッケージ名に合わせて "mmopdca"
#   - explicit UTC 運用
# ----------------------------------------------------------------------
celery_app: Celery = Celery(
    "mmopdca",
    broker=BROKER_URL,
    backend=RESULT_BACKEND_URL,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    # TODO: 外部設定 (settings/*.json) に切り出し
    task_acks_late=True,              # ワーカー落ちた際に再配布
    worker_max_tasks_per_child=100,   # メモリリーク対策
)

# ----------------------------------------------------------------------
# タスク登録
# ----------------------------------------------------------------------
@celery_app.task(name="run_do", autoretry_for=(Exception,), retry_backoff=5, retry_kwargs={"max_retries": 3})
def run_do_task(plan_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Do-phase を非同期で実行する Celery タスク。

    Parameters
    ----------
    plan_id : str
        Plan の ID
    params  : dict[str, Any]
        API レイヤーから渡ってくるパラメータ一式

    Returns
    -------
    dict[str, Any]
        core.do.coredo_executor.run_do が返す JSON 互換辞書
    """
    logger.info("[Celery] run_do_task  plan_id=%s  params_keys=%s", plan_id, list(params.keys()))
    # 遅延 import：ワーカー起動時のロード時間を短縮
    from core.do.coredo_executor import run_do  # noqa: WPS433 (allow import inside func)

    result = run_do(plan_id, params)
    logger.info("[Celery] ✓ completed  plan_id=%s  rows=%s", plan_id, result.get("summary", {}).get("rows"))
    return result


# ----------------------------------------------------------------------
# （任意）定期処理を追加したい場合のテンプレ
# ----------------------------------------------------------------------
# Example:
# celery_app.conf.beat_schedule = {
#     "daily-health-check": {
#         "task": "run_health_check",
#         "schedule": crontab(minute=0, hour=3),  # UTC 03:00 = JST 12:00
#     }
# }
#
# @celery_app.task(name="run_health_check")
# def run_health_check() -> str:
#     logger.info("[Celery] health-check ping")
#     # TODO: 実装
#     return "pong"
#
# ↑必要になるまではコメントアウトのままで OK
