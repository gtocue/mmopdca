# =========================================================
# ASSIST_KEY: このファイルは【utils/audit_stamper.py】に位置するユニットです
# =========================================================
#
# 【概要】
#   このユニットは audit_stamper として、
#   監査ログブロックに RFC-3161 タイムスタンプトークンを組み込む機能を実装します。
#
# 【主な役割】
#   - ログブロック(dict)をJSONシリアライズ
#   - utils/tsa_client.timestamp_request を呼び出し
#   - 返却トークンを 'tsa_token' フィールドに追加して返却
#
# 【連携先・依存関係】
#   - utils/tsa_client.timestamp_request
#   - core/logging.py で呼び出し
#
# 【ルール遵守】
#   1) pdca_data など外部ストアへの直接書き込み禁止
#   2) JSONシリアライズは core/utils.py のサニタイズ関数を利用
#   3) エラー時は例外を投げ、呼び出し側で捕捉
#
# 【注意事項】
#   - ハードコードは # FIXME を付与
#   - 型安全：typing と Pydantic利用可
#
# ---------------------------------------------------------

import json
import logging
from typing import Dict, Any

from utils.tsa_client import timestamp_request
from utils import sanitize_for_serialization  # TODO: sanitize_for_serialization を utils モジュールに実装

logger = logging.getLogger(__name__)


def stamp_audit_block(block: Dict[str, Any]) -> Dict[str, Any]:
    """
    block: 監査ログデータの辞書
    returns: 'tsa_token'フィールドを追加した新しい辞書
    """
    # 1) ディープコピーして破壊的変更を防止
    block_copy = sanitize_for_serialization(block)

    # 2) JSONシリアライズ
    try:
        raw = json.dumps(block_copy, sort_keys=True).encode('utf-8')
    except Exception as e:
        logger.error('Failed to serialize audit block for TSA: %s', e)
        raise

    # 3) TSAトークン取得
    try:
        token = timestamp_request(raw)
    except Exception as e:
        logger.error('Failed to obtain TSA token: %s', e)
        raise

    # 4) 結果を結合
    stamped = dict(block_copy)
    stamped['tsa_token'] = token  # DERバイト列
    return stamped
