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
# REDIS_URL を優先的に読み込み。未設定時は REDIS_PASSWORD／REDIS_HOST から組み立てる
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
REDIS_HOST = os.environ.get("REDIS_HOST", "redis")
broker_url = os.environ.get(
    "REDIS_URL",
    f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:6379/0"
)

# CELERY_RESULT_BACKEND を優先的に読み込み。未設定時は broker_url の別データベースにする
result_backend = os.environ.get("CELERY_RESULT_BACKEND", broker_url.replace("/0", "/1"))

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
always_eager = os.environ.get("CELERY_TASK_ALWAYS_EAGER", "false").lower() in ("1", "true", "yes")
eager_propagates = os.environ.get("CELERY_TASK_EAGER_PROPAGATES", "false").lower() in ("1", "true", "yes")

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
celery_app.autodiscover_tasks(["core.tasks.do_tasks"], related_name="tasks", force=True)
