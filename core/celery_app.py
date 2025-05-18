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

    # 例：run_do_task を毎時 0 分に呼び出す
    "run-do-task-every-hour": {
        "task": "core.tasks.do_tasks.run_do_task",
        # 毎時 0 分に実行
        "schedule": crontab(minute=0),
        # ここを運用実行時の引数に置き換えてください
        "args": (
            "do-<your-id>-every-hour",    # do_id
            "plan-<your-plan-id>",        # plan_id
            {"param1": "foo", "param2": 42},  # params
        ),
    },

    # 例：毎日深夜 1 時に実行するタスク
    "daily-retrain-plan": {
        "task": "core.tasks.do_tasks.run_do_task",
        "schedule": crontab(hour=1, minute=0),
        "args": (
            "do-retrain-{{ds}}",    # 任意の識別子（例: 日付埋込み可）
            "plan-retrain",         # リトレイン用プランID
            {"epochs": 5},          # 任意のパラメータ
        ),
    },

    # 他のタスクを追加する場合は、同様にキーを定義してください...
}

# ----------------------------------------------------------------------
# タスク定義の自動読み込み
# core/tasks/do_tasks.py 内の @shared_task デコレータ付きタスクを登録
# ----------------------------------------------------------------------
celery_app.autodiscover_tasks(
    ["core.tasks.do_tasks"],
    related_name="tasks",
    force=True,
)
