# core/tasks/demo.py
from celery import shared_task


@shared_task(name="demo.add")
def add(x: int, y: int) -> int:
    """シンプルな足し算タスク（Smoke Test 用）"""
    return x + y
