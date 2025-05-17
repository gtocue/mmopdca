# =========================================================
# ASSIST_KEY: このファイルは【utils/redis_client.py】に位置するユニットです
# =========================================================
#
# 【概要】
#   Redis クライアントを取得し、FastAPI の依存注入として提供します。
#
# 【主な役割】
#   - 環境変数 REDIS_URL から接続先を取得
#   - Redis クライアント（redis-py）を返却
#   - 接続失敗時は HTTPException 500 を返す
#
# 【連携先・依存関係】
#   - redis ライブラリ (redis>=4.0.0)
#   - fastapi HTTPException
#
# 【ルール遵守】
#   1) グローバル変数直書き禁止
#   2) 環境変数が未設定ならデフォルト URL を使用
#   3) 例外時は適切にログと HTTPException を発生
#
# ---------------------------------------------------------

import os
from redis import Redis
from fastapi import HTTPException

def get_redis() -> Redis:
    """
    FastAPI 依存注入用に Redis クライアントを生成して返します。
    REDIS_URL 環境変数が未設定の場合は redis://localhost:6379/0 を使用します。
    """
    url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    try:
        client = Redis.from_url(url)
        # 簡易接続チェック
        client.ping()
        return client
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cannot connect to Redis: {e}")
