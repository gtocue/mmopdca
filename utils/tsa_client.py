# =========================================================
# ASSIST_KEY: このファイルは【utils/tsa_client.py】に位置するユニットです
# =========================================================
#
# 【概要】
#   このユニットは tsa_client として、
#   RFC-3161 準拠のタイムスタンプリクエストおよびレスポンスの送受信・検証機能を実装／提供します。
#
# 【主な役割】
#   - TSA サーバーへのタイムスタンプリクエスト生成
#   - レスポンス受信後の検証およびトークン抽出
#   - エラー発生時のログ出力管理
#
# 【連携先・依存関係】
#   - 他ユニット :
#       ・core/logging.py            （ロガー設定）
#       ・core/utils.py              （シリアライズ・デシリアライズ）
#   - 外部設定 :
#       ・.env に定義された TSA_URL 環境変数
#
# 【ルール遵守】
#   1) 環境変数以外のハードコードは禁止 (# FIXME: ハードコード があればコメント)
#   2) 型安全のため typing を活用
#   3) 外部設定未実装なら TODO: 要確認
#   4) pdca_data[...] 直接書き込み禁止
#
# 【注意事項】
#   - ハルシネーション厳禁
#   - 例外は必ず logging.error で記録
#   - 機能追加は事前相談（破壊的変更NG）
#
# ---------------------------------------------------------

import os
import logging
from typing import ByteString

from rfc3161ng import TimestampRequest, TimestampClient, TSR

logger = logging.getLogger(__name__)

# TSA サーバー URL は環境変数から取得
TSA_URL = os.getenv("TSA_URL")  # TODO: 要確認 - .env.exampleに追加する
if not TSA_URL:
    logger.error("TSA_URL is not set in environment variables")
    # FIXME: 環境変数未設定時のフェイルセーフを検討


def timestamp_request(data: ByteString) -> bytes:
    """
    data: バイト列 (例: ログブロックの JSON を UTF-8 エンコードしたもの)
    returns: RFC-3161 タイムスタンプトークン (DER バイト列)
    """
    # 1) リクエスト生成 (SHA-256 ダイジェスト)
    ts_req = TimestampRequest(
        data=data,
        digest="sha256",
        cert_req=True  # TSA証明書を含むよう依頼
    )

    # 2) TSA に送信
    client = TimestampClient(TSA_URL, verify_tls=TSA_URL.startswith("https://"))
    try:
        tsr: TSR = client.send(ts_req)
    except Exception as e:
        logger.error("TSA request failed: %s", e)
        raise

    # 3) 応答検証
    try:
        tsr.verify(ts_req)
    except Exception as e:
        logger.error("TSA response verification failed: %s", e)
        raise

    # 4) トークンを返却
    return tsr.content  # DER バイト列
