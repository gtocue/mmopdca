# ---- build / runtime 共通 ----------------------------------------
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DSL_ROOT=/mnt/data/dsl

RUN apt-get update \
    && apt-get install -y --no-install-recommends dos2unix \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ---- Poetry + deps ----------------------------------------------
COPY pyproject.toml poetry.lock ./
RUN pip install --no-cache-dir --upgrade pip poetry \
    && poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --without dev --no-root

# ---- アプリケーションコードをコピー & 初期化スクリプト設置 ------------
COPY . .
COPY ops/init-dsl.sh /usr/local/bin/docker-entrypoint-init-dsl.sh
RUN dos2unix /usr/local/bin/docker-entrypoint-init-dsl.sh \
    && chmod +x /usr/local/bin/docker-entrypoint-init-dsl.sh

# ── チェックポイント用ディレクトリ作成＋所有権調整 -------------
USER root
RUN mkdir -p /mnt/checkpoints \
    && chown 1000:1000 /mnt/checkpoints

# デフォルトで非 root に戻す
USER 1000:1000

# ENTRYPOINT / コマンドは Compose 側で指定
