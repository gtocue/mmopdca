# tests/test_tasks_s3_md5.py

import logging
import pytest

from core.tasks.do_tasks import s3_md5_check

@pytest.fixture(autouse=True)
def set_log_level(caplog):
    # 全テストで INFO レベル以上をキャプチャ
    caplog.set_level(logging.INFO)
    return caplog

def test_s3_md5_check_success(monkeypatch, set_log_level):
    """
    check_s3_md5 が (True, expected, actual) を返した場合、
    logger.info に OK が出力されることを確認する。
    """
    # モック：バケット/キーに対して常に一致を返す
    monkeypatch.setattr(
        "core.tasks.do_tasks.check_s3_md5",
        lambda bucket, key: (True, "abc123", "abc123"),
    )

    # タスクを同期実行
    s3_md5_check.run("my-bucket", "path/to/script.py")

    # ログに [md5-check] が含まれ、OK が表示されていること
    messages = [rec.message for rec in set_log_level.records]
    assert any(
        "[md5-check] my-bucket/path/to/script.py → OK (expected=abc123 actual=abc123)"
        == msg
        for msg in messages
    ), f"ログが不正です: {messages}"

def test_s3_md5_check_mismatch(monkeypatch, set_log_level):
    """
    check_s3_md5 が (False, expected, actual) を返した場合、
    logger.info に MISMATCH が出力されることを確認する。
    """
    monkeypatch.setattr(
        "core.tasks.do_tasks.check_s3_md5",
        lambda bucket, key: (False, "aaa111", "bbb222"),
    )

    s3_md5_check.run("my-bucket", "another/key.txt")

    messages = [rec.message for rec in set_log_level.records]
    assert any(
        "[md5-check] my-bucket/another/key.txt → MISMATCH (expected=aaa111 actual=bbb222)"
        == msg
        for msg in messages
    ), f"ログが不正です: {messages}"

def test_s3_md5_check_exception(monkeypatch, set_log_level):
    """
    check_s3_md5 が例外を投げた場合、タスクも例外を再送出し、
    logger.error にエラー情報が出力されることを確認する。
    """
    def _raise(bucket, key):
        raise RuntimeError("S3 access failed")

    monkeypatch.setattr("core.tasks.do_tasks.check_s3_md5", _raise)

    with pytest.raises(RuntimeError, match="S3 access failed"):
        s3_md5_check.run("err-bucket", "bad/key.dat")

    # エラーログの先頭に [md5-check] エラーが含まれる
    messages = [rec.message for rec in set_log_level.records]
    assert any(
        msg.startswith("[md5-check] エラー err-bucket/bad/key.dat")
        for msg in messages
    ), f"エラーログが不正です: {messages}"
