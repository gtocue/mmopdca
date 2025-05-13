# ASSIST_KEY: このファイルは【utils/__init__.py】に位置するユニットです

import copy
import datetime
import decimal
from typing import Any

def sanitize_for_serialization(obj: Any) -> Any:
    """
    JSON シリアライズ可能な構造に再帰的に変換／コピーします。
    - dict -> new dict
    - list/tuple/set -> list
    - datetime, date -> ISO 文字列
    - Decimal -> str
    - Pydantic BaseModel -> .dict()
    - その他 -> str(obj)
    """
    # Pydantic モデル対応
    try:
        # type: ignore
        from pydantic import BaseModel
        if isinstance(obj, BaseModel):
            return sanitize_for_serialization(obj.dict())
    except ImportError:
        pass

    # プリミティブ型
    if obj is None or isinstance(obj, (bool, int, float, str)):
        return obj
    # 日付時刻
    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    # Decimal
    if isinstance(obj, decimal.Decimal):
        return str(obj)
    # dict
    if isinstance(obj, dict):
        return {str(k): sanitize_for_serialization(v) for k, v in obj.items()}
    # iterable
    if isinstance(obj, (list, tuple, set)):
        return [sanitize_for_serialization(v) for v in obj]
    # その他フォールバック
    return str(obj)
