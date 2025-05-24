"""
api.routers.ai_key_api
----------------------

Sprint-2: “AI-Key PoC” 用のシンプルなキー管理エンドポイント。
外部サービスへはアクセスせず、**インメモリ** で完結させているため
ユニットテストでもネットワークエラーになりません。

❌ 永続化なし
❌ 本番環境用途なし
✅ 生成・一覧・削除 が出来ればテストは通る
"""

from __future__ import annotations

import secrets
from typing import Final, List

from fastapi import APIRouter, HTTPException, status

router: Final = APIRouter(prefix="/ai-key", tags=["ai-key"])

# メモリ上にだけ保持（PoC 用）
_KEYS: list[str] = []


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_key() -> dict[str, str]:
    """32 文字のランダム API キーを発行して返す。"""
    key = secrets.token_hex(16)
    _KEYS.append(key)
    return {"key": key}


@router.get("/", response_model=List[str])
def list_keys() -> list[str]:
    """現在登録されているキーをすべて返す。"""
    return _KEYS.copy()


@router.delete("/{key}", status_code=status.HTTP_204_NO_CONTENT)
def delete_key(key: str) -> None:
    """指定キーを削除。存在しなければ 404。"""
    try:
        _KEYS.remove(key)
    except ValueError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "key not found") from exc
