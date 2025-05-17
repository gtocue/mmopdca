# =========================================================
# ASSIST_KEY: このファイルは【utils/event_serializer.py】に位置するユニットです
# =========================================================
#
# 【概要】
#   Redis Stream エントリを SSE 用 JSON ペイロードに変換するユーティリティ。
#
# 【主な役割】
#   - Redis の entry_id と data 辞書を JSON シリアライズ可能な形式にマッピング
#   - bytes を UTF-8 デコードし、適切な型に変換
#
# 【連携先・依存関係】
#   - Redis xrevrange/xread が返す (entry_id, data) 形式
#
# 【ルール遵守】
#   1) ローカル変数直書き禁止
#   2) デコードエラーは例外発生させず安全にスキップ
#
# ---------------------------------------------------------

import json
from typing import Any, Dict, Union


def serialize_event(entry_id: Union[str, bytes], data: Dict[Union[str, bytes], Any]) -> Dict[str, Any]:
    """
    Redis Stream のエントリを JSON 形式で返却する。

    Args:
        entry_id: Redis Stream entry ID (bytes or str)
        data:      フィールド名と値の辞書 (bytes または str)

    Returns:
        JSON シリアライズ可能な dict: {'id': entry_id, **fields}
    """
    # ID を文字列化
    if isinstance(entry_id, bytes):
        id_str = entry_id.decode('utf-8', errors='ignore')
    else:
        id_str = str(entry_id)

    payload: Dict[str, Any] = {'id': id_str}

    # 各フィールドをデコード
    for key, value in data.items():
        # key
        if isinstance(key, bytes):
            k = key.decode('utf-8', errors='ignore')
        else:
            k = str(key)

        # value
        if isinstance(value, bytes):
            v_decoded = value.decode('utf-8', errors='ignore')
            # 値が JSON 文字列ならロードを試みる
            try:
                v = json.loads(v_decoded)
            except (json.JSONDecodeError, TypeError):
                v = v_decoded
        else:
            v = value

        payload[k] = v

    return payload
