# =========================================================
# ASSIST_KEY: このファイルは【tests/test_tsa_stamp.py】に位置するユニットです
# =========================================================
#
# 【概要】
#   このユニットは test_tsa_stamp として、
#   utils/tsa_client.timestamp_request のユニットテストを提供します。
#
# 【主な役割】
#   - timestamp_request が TSA モック呼び出しで正しくトークンを返すことを検証
#   - TSA 送信失敗時にエラーをログに記録し例外を送出することを検証
#   - TSA 応答検証失敗時にエラーをログに記録し例外を送出することを検証
#
# 【連携先・依存関係】
#   - テスト対象: utils/tsa_client.py
#   - モック: rfc3161ng.TimestampClient.send
#
# 【ルール遵守】
#   1) ハードコード値はテスト内限定 (# FIXME: を含まない)
#   2) ログ出力は caplog を用いて検証
#   3) テストは pytest で実行可能
#   4) 型安全: typing を活用
#
# 【注意事項】
#   - ハルシネーション厳禁
#   - fixtures はすべてテスト内に実装
#
# ---------------------------------------------------------

import json
import logging
import pytest

from utils.tsa_client import timestamp_request

# 成功パス: モックTSRが正しくcontentを返す
def test_timestamp_request_success(monkeypatch):
    class FakeTSR:
        content = b"FAKE_DER_TOKEN"
        def verify(self, req):
            # 正常パスでは例外なし
            pass

    def fake_send(self, req):
        return FakeTSR()

    # rfc3161ng.TimestampClient.sendをモック
    monkeypatch.setattr("rfc3161ng.TimestampClient.send", fake_send)

    payload = {"block": 1, "hash": "abc"}
    data = json.dumps(payload).encode("utf-8")
    token = timestamp_request(data)
    assert token == b"FAKE_DER_TOKEN"


# 送信失敗時: TSA unreachable
def test_timestamp_request_send_failure(monkeypatch, caplog):
    def fake_send(self, req):
        raise RuntimeError("TSA unreachable")

    monkeypatch.setattr("rfc3161ng.TimestampClient.send", fake_send)
    caplog.set_level(logging.ERROR)

    with pytest.raises(RuntimeError):
        timestamp_request(b"dummy")

    assert "TSA request failed" in caplog.text


# 応答検証失敗時: verifyで例外
def test_timestamp_response_verification_failure(monkeypatch, caplog):
    class FakeTSR:
        content = b"dummy"
        def verify(self, req):
            raise ValueError("Invalid TSA token")

    def fake_send(self, req):
        return FakeTSR()

    monkeypatch.setattr("rfc3161ng.TimestampClient.send", fake_send)
    caplog.set_level(logging.ERROR)

    with pytest.raises(ValueError):
        timestamp_request(b"dummy")

    assert "TSA response verification failed" in caplog.text
