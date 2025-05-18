# ----------------------------------------------------------------------
# File: core/celery_app.py
# Name: Celery アプリ定義
# Summary: broker/backend と Eager モード設定を環境変数から読み込む
# ----------------------------------------------------------------------

import os
from pathlib import Path
from dotenv import load_dotenv
from celery import Celery
from celery.schedules import crontab

# ----------------------------------------------------------------------
# .env ファイルを読み込む（ローカル開発用／CI 用どちらにも対応）
# ----------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
dotenv_path = BASE_DIR / (os.getenv("ENV_FILE", ".env"))
load_dotenv(dotenv_path=dotenv_path)

# ----------------------------------------------------------------------
# Celery ブローカー／バックエンド設定
# ----------------------------------------------------------------------
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
default_broker = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:6379/0"
broker_url = os.getenv("CELERY_BROKER_URL", default_broker)

default_backend = broker_url.replace("/0", "/1")
result_backend = os.getenv("CELERY_RESULT_BACKEND", default_backend)

celery_app = Celery(
    "mmopdca",
    broker=broker_url,
    backend=result_backend,
)

# ----------------------------------------------------------------------
# Eager モード設定（同期実行・例外伝播）
# ----------------------------------------------------------------------
always_eager = os.getenv("CELERY_TASK_ALWAYS_EAGER", "false").lower() in (
    "1", "true", "yes"
)
eager_propagates = os.getenv("CELERY_TASK_EAGER_PROPAGATES", "false").lower() in (
    "1", "true", "yes"
)

celery_app.conf.update(
    task_always_eager=always_eager,
    task_eager_propagates=eager_propagates,
    task_store_eager_result=always_eager,
)

# ----------------------------------------------------------------------
# 定期実行ジョブ (beat_schedule) 定義
# ----------------------------------------------------------------------
celery_app.conf.beat_schedule = {
    # 毎分出力テスト用
    "print-heartbeat-every-minute": {
        "task": "core.tasks.do_tasks.print_heartbeat",
        "schedule": crontab(minute="*/1"),
    },

    # 実運用：S3 MD5 チェックを毎時 0 分に実行
    "s3-md5-check-every-hour": {
        "task": "core.tasks.do_tasks.s3_md5_check",
        "schedule": crontab(minute=0),
        # ここは実際のバケット名／キーに置き換えてください
        "args": ("your-dsl-bucket-name", "path/to/your/script.py"),
    },

    # メイン Do タスクを毎時 0 分に呼び出す例
    "run-do-task-every-hour": {
        "task": "core.tasks.do_tasks.run_do_task",
        "schedule": crontab(minute=0),
        "args": (
            "do-hourly-0001",         # do_id
            "plan-hourly-execution",  # plan_id
            {"param1": "foo", "param2": 42},  # params
        ),
    },

    # 日次深夜 1:00 実行タスク例
    "daily-retrain-plan": {
        "task": "core.tasks.do_tasks.run_do_task",
        "schedule": crontab(hour=1, minute=0),
        "args": (
            "do-retrain-{{ds}}",  # 任意フォーマット可
            "plan-retrain",
            {"epochs": 5},
        ),
    },
}

# ----------------------------------------------------------------------
# タスク定義の自動読み込み
# core/tasks/do_tasks.py 内の @celery_app.task デコレータ付きタスクを登録
# ----------------------------------------------------------------------
celery_app.autodiscover_tasks(
    ["core.tasks.do_tasks"],
    related_name="tasks",
    force=True,
)
