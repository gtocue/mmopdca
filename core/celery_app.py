# ----------------------------------------------------------------------
# File: core/celery_app.py
# Name: Celery アプリ定義
# Summary: broker/backend と Eager モード設定を環境変数から読み込む
# ----------------------------------------------------------------------

import os
from pathlib import Path
from dotenv import load_dotenv
from celery import Celery

# ----------------------------------------------------------------------
# .env ファイルを読み込む（ローカル開発用／CI 用どちらにも対応）
# ----------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
dotenv_path = BASE_DIR / (os.getenv("ENV_FILE", ".env"))
load_dotenv(dotenv_path=dotenv_path)

# ----------------------------------------------------------------------
# Celery ブローカー／バックエンド設定
# ----------------------------------------------------------------------
# Redis 用設定
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
# デフォルトの broker_url
default_broker = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:6379/0"
# 環境変数 CELERY_BROKER_URL があれば優先
broker_url = os.getenv("CELERY_BROKER_URL", default_broker)

# デフォルトの result_backend は broker の DB1
default_backend = broker_url.replace("/0", "/1")
# 環境変数 CELERY_RESULT_BACKEND があれば優先
result_backend = os.getenv("CELERY_RESULT_BACKEND", default_backend)

# Celery アプリケーションのインスタンス化
celery_app = Celery(
    "mmopdca",
    broker=broker_url,
    backend=result_backend,
)

# ----------------------------------------------------------------------
# Eager モード設定（同期実行・例外伝播）
# ----------------------------------------------------------------------
# CI／テスト環境では .env.ci から以下の環境変数を渡す想定
always_eager = os.getenv("CELERY_TASK_ALWAYS_EAGER", "false").lower() in (
    "1",
    "true",
    "yes",
)
eager_propagates = os.getenv("CELERY_TASK_EAGER_PROPAGATES", "false").lower() in (
    "1",
    "true",
    "yes",
)

# Eager モードの設定を更新
celery_app.conf.update(
    # タスクを同期実行するかどうか
    task_always_eager=always_eager,
    # Eager モードで例外を即座にアプリ側に伝播させる
    task_eager_propagates=eager_propagates,
    # Eager モード実行時にも結果をバックエンドに保存する
    task_store_eager_result=always_eager,
)

# ----------------------------------------------------------------------
# タスク定義の自動読み込み
# core/tasks/do_tasks.py 内の @shared_task デコレータ付きタスクを登録
# ----------------------------------------------------------------------
celery_app.autodiscover_tasks([
    "core.tasks.do_tasks"
], related_name="tasks", force=True)
