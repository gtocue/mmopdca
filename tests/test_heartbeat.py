# tests/test_heartbeat.py

import pytest
from celery.schedules import crontab

from core.celery_app import celery_app
from core.tasks.do_tasks import print_heartbeat

def test_heartbeat_is_in_beat_schedule():
    """
    beat_schedule に print-heartbeat-every-minute が含まれていることを確認。
    """
    beat_schedule = celery_app.conf.beat_schedule or {}
    assert "print-heartbeat-every-minute" in beat_schedule, \
        "定期タスク 'print-heartbeat-every-minute' が beat_schedule に登録されていません。"

    cfg = beat_schedule["print-heartbeat-every-minute"]
    # タスク名の確認
    assert cfg["task"] == "core.tasks.do_tasks.print_heartbeat"
    # 1分間隔の crontab であることを確認
    schedule = cfg["schedule"]
    assert isinstance(schedule, crontab), "schedule が crontab オブジェクトではありません。"
    # 表現に */1（毎分実行）が含まれていることを確認
    assert "*/1" in str(schedule), f"schedule に '*/1' が含まれていません: {schedule}"

def test_print_heartbeat_outputs_timestamp(capfd):
    """
    print_heartbeat() を呼び出すと標準出力に [heartbeat] タグ付きのタイムスタンプが出力されることを確認。
    """
    # 直接実行
    print_heartbeat()

    captured = capfd.readouterr()
    out = captured.out.strip()
    assert out.startswith("[heartbeat] "), f"出力フォーマットが不正です: {out}"
    # UTC ISO フォーマットが続いている
    iso_ts = out.split(" ", 1)[1]
    # 大まかに ISO8601 互換になっていれば OK
    assert ("T" in iso_ts and iso_ts.endswith("Z")) or ("+" in iso_ts), \
        f"タイムスタンプ形式が不正です: {iso_ts}"
