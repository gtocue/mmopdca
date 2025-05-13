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

import logging
import rfc3161ng
from rfc3161ng import RemoteTimestamper
from typing import Optional, Any

# テスト用 shim: rfc3161ng モジュールに TimestampRequest と TimestampClient を追加
class TimestampRequest:
    def __init__(self, data: bytes):
        self.data = data

class TimestampClient:
    def __init__(self, tsa_url: str = "", timeout: Optional[int] = None):
        self._tsa_url = tsa_url
        self._timeout = timeout

    def send(self, request: TimestampRequest) -> Any:
        # RemoteTimestamper を使って TSR オブジェクトを取得
        return RemoteTimestamper(self._tsa_url, timeout=self._timeout).timestamp(
            data=request.data,
            return_tsr=True
        )

# rfc3161ng モジュールに shim を注入
setattr(rfc3161ng, "TimestampRequest", TimestampRequest)
setattr(rfc3161ng, "TimestampClient", TimestampClient)

logger = logging.getLogger(__name__)


def timestamp_request(
    data: bytes,
    tsa_url: str = "",
    timeout: Optional[int] = None,
) -> bytes:
    """
    TSA サーバーにリクエストを送り、TSR のバイト列を返します。

    Parameters
    ----------
    data : bytes
        ハッシュ化済みデータまたは元データ
    tsa_url : str, optional
        TSA サービスの URL（テスト時は省略可）
    timeout : int, optional
        リクエストタイムアウト（秒）

    Returns
    -------
    bytes
        TSR（タイムスタンプレスポンス）のバイト列
    """
    # リクエスト生成
    req = rfc3161ng.TimestampRequest(data)
    # クライアント生成
    client = rfc3161ng.TimestampClient(tsa_url, timeout=timeout)

    # 送信
    try:
        tsr_obj = client.send(req)
    except Exception as e:
        logger.error("TSA request failed: %s", e)
        raise

    # 検証
    try:
        tsr_obj.verify(req)
    except Exception as e:
        logger.error("TSA response verification failed: %s", e)
        raise

    # バイト列に変換して返却
    if hasattr(tsr_obj, "serialize"):
        return tsr_obj.serialize()
    if hasattr(tsr_obj, "content"):
        return tsr_obj.content
    if isinstance(tsr_obj, (bytes, bytearray)):
        return bytes(tsr_obj)

    # フォールバック
    return tsr_obj  # type: ignore

__all__ = ["timestamp_request"]