# ========================================================
# File: Dockerfile
# Name: MMOPDCA マルチステージビルド定義（3層構造）
# Summary:
#   1) builder: Poetry で依存解決とソース配置
#   2) runtime: ライブラリとエントリポイントのみコピーした軽量イメージ
#   3) api: runtime を継承し、API 実行コマンドを設定
# ========================================================

# --------------------------------------------------------
# 1) builder: Poetry でロックファイル生成＋依存解決
# --------------------------------------------------------
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# ビルドに必要なツールをインストール
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    dos2unix \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Poetry インストール＆設定、依存解決
COPY pyproject.toml poetry.lock* ./
RUN pip install --no-cache-dir --upgrade pip poetry \
    && poetry config virtualenvs.create false \
    && poetry lock --no-update \
    && poetry install --no-interaction --no-ansi --without dev

# アプリケーションコードをコピー
COPY . .

# DSL 初期化スクリプトを配置・整形・実行権限付与
COPY ops/init-dsl.sh /usr/local/bin/docker-entrypoint-init-dsl.sh
RUN dos2unix /usr/local/bin/docker-entrypoint-init-dsl.sh \
    && chmod +x /usr/local/bin/docker-entrypoint-init-dsl.sh


# --------------------------------------------------------
# 2) runtime: ライブラリとスクリプトのみを持つ軽量環境
# --------------------------------------------------------
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DSL_ROOT=/mnt/data/dsl

# ファイルアップロード用 multipart と最低限ツールをインストール
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    dos2unix \
    python3-multipart \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# builder からパッケージとソースをコピー
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /app /app

# init スクリプトをコピー（パーミッションは builder 側で設定済み）
COPY --from=builder /usr/local/bin/docker-entrypoint-init-dsl.sh /usr/local/bin/

# DSL・チェックポイント格納ディレクトリを作成・所有権設定
USER root
RUN mkdir -p /mnt/data/dsl /mnt/checkpoints \
    && chown 1000:1000 /mnt/data/dsl /mnt/checkpoints

# デフォルトユーザーを戻す
USER 1000:1000


# --------------------------------------------------------
# 3) api: runtime 環境を継承し、実行コマンドを設定
# --------------------------------------------------------
FROM runtime AS api

# コンテナ外部に公開するポート
EXPOSE 8001

# エントリポイントとコマンドの組み合わせ
ENTRYPOINT ["/usr/local/bin/docker-entrypoint-init-dsl.sh"]
CMD ["uvicorn", "api.main_api:app", \
    "--host", "0.0.0.0", "--port", "8001", "--proxy-headers"]
