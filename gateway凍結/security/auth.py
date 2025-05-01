# =========================================================
# ASSIST_KEY: このファイルは【gateway/security/auth.py】に位置するユニットです
# =========================================================
#
# 【概要】
#   このユニットは Auth ヘルパーとして、
#   JWT (Bearer) または X-API-Key ヘッダを検証し FastAPI 依存注入を提供します。
#
# 【主な役割】
#   - `verify_token` : FastAPI Depends 用の認証関数
#   - `decode_jwt`   : HS256 署名を検証し payload(dict) を返す
#
# 【連携先・依存関係】
#   - gateway/api/router.py で Depends される
#   - .env  :
#       ・JWT_SECRET   – HS256 シークレットキー
#       ・API_KEYS     – カンマ区切り有効キー
#
# 【ルール遵守】
#   1) 例外は fastapi.HTTPException(401) で統一
#   2) グローバル変数直書き禁止（環境変数経由）
#   3) 型安全重視・ハルシネーション厳禁
# ---------------------------------------------------------

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Final

import jwt
from fastapi import Depends, Header, HTTPException, status

logger = logging.getLogger(__name__)

JWT_SECRET: Final[str] = os.getenv("JWT_SECRET", "mmop-gateway-dev-secret")  # FIXME: ハードコード
API_KEYS: Final[set[str]] = {
    key.strip() for key in os.getenv("API_KEYS", "").split(",") if key.strip()
}


def decode_jwt(token: str) -> dict:
    """
    HS256 署名を検証して payload を返す。
    検証失敗時は HTTP 401 を raise。
    """
    try:
        payload: dict = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except jwt.PyJWTError as exc:  # noqa: BLE001
        logger.warning("JWT decode error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        ) from exc

    # exp チェック（秒精度）
    exp = payload.get("exp")
    if exp and datetime.now(timezone.utc).timestamp() > exp:
        raise HTTPException(status_code=401, detail="Token expired")

    return payload


async def verify_token(
    authorization: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
):
    """
    FastAPI 依存注入関数。
    - Bearer <JWT> または X-API-Key いずれかを許可
    """
    if authorization and authorization.startswith("Bearer "):
        token = authorization.removeprefix("Bearer ").strip()
        return decode_jwt(token)

    if x_api_key and x_api_key in API_KEYS:
        return {"api_key": x_api_key}

    logger.info("auth failed: no valid credentials")
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Unauthorized",
    )
