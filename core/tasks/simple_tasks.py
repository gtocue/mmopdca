# core/tasks/simple_tasks.py
from __future__ import annotations

from celery import shared_task


# デモ用タスク。name= でフルパスを固定しておくと安全。
@shared_task(name="core.tasks.do_tasks.add")
def add(x: int, y: int) -> int:
    return x + y
