# tests/unit/test_celery_heartbeat.py

import pytest
from celery.schedules import crontab

from core.celery_app import celery_app
from core.tasks.do_tasks import print_heartbeat

def test_heartbeat_in_beat_schedule():
    beat = celery_app.conf.beat_schedule or {}
    assert "print-heartbeat-every-minute" in beat

    cfg = beat["print-heartbeat-every-minute"]
    assert cfg["task"] == "core.tasks.do_tasks.print_heartbeat"
    assert isinstance(cfg["schedule"], crontab)
    assert "*/1" in str(cfg["schedule"])

def test_print_heartbeat_format(capfd):
    print_heartbeat()
    out = capfd.readouterr().out.strip()
    assert out.startswith("[heartbeat] ")
    ts = out.split(" ", 1)[1]
    assert ("T" in ts and ts.endswith("Z")) or ("+" in ts)
