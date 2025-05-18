# tests/test_s3_md5_check.py
# tests/unit/test_tasks_s3_md5.py

import logging
import pytest

from core.tasks.do_tasks import s3_md5_check

@pytest.fixture(autouse=True)
def cap_info(caplog):
    caplog.set_level(logging.INFO)
    return caplog

def test_s3_md5_check_success(monkeypatch, cap_info):
    monkeypatch.setattr(
        "core.tasks.do_tasks.check_s3_md5",
        lambda bucket, key: (True, "abc123", "abc123"),
    )
    s3_md5_check.run("my-bucket", "path/to/script.py")

    msgs = [r.message for r in cap_info.records]
    assert any(
        "[md5-check] my-bucket/path/to/script.py → OK (expected=abc123 actual=abc123)" in m
        for m in msgs
    )

def test_s3_md5_check_mismatch(monkeypatch, cap_info):
    monkeypatch.setattr(
        "core.tasks.do_tasks.check_s3_md5",
        lambda bucket, key: (False, "aaa111", "bbb222"),
    )
    s3_md5_check.run("my-bucket", "another/key.txt")

    msgs = [r.message for r in cap_info.records]
    assert any(
        "[md5-check] my-bucket/another/key.txt → MISMATCH (expected=aaa111 actual=bbb222)" in m
        for m in msgs
    )

def test_s3_md5_check_exception(monkeypatch, cap_info):
    def _raise(bucket, key):
        raise RuntimeError("S3 access failed")
    monkeypatch.setattr("core.tasks.do_tasks.check_s3_md5", _raise)

    with pytest.raises(RuntimeError):
        s3_md5_check.run("err-bucket", "bad/key.dat")

    msgs = [r.message for r in cap_info.records]
    assert any(
        m.startswith("[md5-check] エラー err-bucket/bad/key.dat")
        for m in msgs
    )
