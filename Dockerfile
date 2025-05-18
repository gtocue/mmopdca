# ========================================================
# File: Dockerfile
# Name: MMOPDCA マルチステージビルド定義
# Summary:
#   - build フェーズで Poetry ロック＋依存解決
#   - runtime フェーズで軽量イメージ利用
#   - DSL データとチェックポイント格納ディレクトリを準備
# ========================================================

# --------------------------------------------------------
# 1) ビルドフェーズ: Poetry でロックファイル生成＋依存解決
# --------------------------------------------------------
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# build に必要なツールを一括インストール
RUN apt-get update \
    && apt-get install -y --no-install-recommends dos2unix curl build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# poetry インストール／設定
COPY pyproject.toml poetry.lock* ./
RUN pip install --no-cache-dir --upgrade pip poetry \
    && poetry config virtualenvs.create false \
    # ロックファイルがない場合もここで生成される
    && poetry lock \
    && poetry install --no-interaction --no-ansi --without dev

# アプリケーションコードをビルド環境へコピー
COPY . .

# initスクリプトを整形＋実行権限付与
COPY ops/init-dsl.sh /usr/local/bin/docker-entrypoint-init-dsl.sh
RUN dos2unix /usr/local/bin/docker-entrypoint-init-dsl.sh \
    && chmod +x /usr/local/bin/docker-entrypoint-init-dsl.sh

# --------------------------------------------------------
# 2) ランタイムフェーズ: 軽量イメージ＋最小限のツール
# --------------------------------------------------------
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DSL_ROOT=/mnt/data/dsl

# runtime に必要なツールを最小限インストール
RUN apt-get update \
    && apt-get install -y --no-install-recommends dos2unix \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ビルドステージからライブラリ群とソースをコピー
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /app /app

# initスクリプトをコピー（すでに権限済み）
COPY --from=builder /usr/local/bin/docker-entrypoint-init-dsl.sh /usr/local/bin/docker-entrypoint-init-dsl.sh

# DSL およびチェックポイント用ディレクトリを非root ユーザーで作成・所有権設定
USER root
RUN mkdir -p /mnt/data/dsl /mnt/checkpoints \
    && chown 1000:1000 /mnt/data/dsl /mnt/checkpoints

# デフォルトで非 root ユーザーに戻す
USER 1000:1000

# ENTRYPOINT / CMD は外部（docker-compose.yml）で指定してください
