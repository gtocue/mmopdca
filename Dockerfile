# ========================================================
# File: Dockerfile
# Name: MMOPDCA core マルチステージビルド定義
# ========================================================

# --------------------------------------------------------
# 1) builder: Poetry で依存解決＋ソース配置
# --------------------------------------------------------
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# ビルドに必要なツールを一括インストール
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    dos2unix \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Poetry インストール＆依存解決
COPY pyproject.toml poetry.lock* README.md ./
RUN pip install --no-cache-dir --upgrade pip poetry \
    && rm -f poetry.lock \
    && poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --without dev --no-root

# アプリケーションコードをコピー
COPY . .

# DSL 初期化スクリプトをコピー→整形→実行権限付与
COPY ops/init-dsl.sh /usr/local/bin/docker-entrypoint-init-dsl.sh
RUN dos2unix /usr/local/bin/docker-entrypoint-init-dsl.sh \
    && chmod +x /usr/local/bin/docker-entrypoint-init-dsl.sh


# --------------------------------------------------------
# 2) runtime: ビルド済みライブラリ＋スクリプトを持つ軽量環境
# --------------------------------------------------------
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DSL_ROOT=/mnt/data/dsl

# 最低限のツールだけインストール
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    dos2unix \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# builder からライブラリとコード、スクリプトをコピー
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /app /app
COPY --from=builder /usr/local/bin/docker-entrypoint-init-dsl.sh /usr/local/bin/

# DSL／チェックポイント用ディレクトリを用意して所有権設定
USER root
RUN mkdir -p /mnt/data/dsl /mnt/checkpoints \
    && chown 1000:1000 /mnt/data/dsl /mnt/checkpoints

# デフォルトユーザーに戻す
USER 1000:1000

# ※Entrypoint/CMD は docker-compose.yml 側で指定します
