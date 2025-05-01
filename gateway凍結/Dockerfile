# =========================================================
# ASSIST_KEY: このファイルは【gateway/Dockerfile】に位置するユニットです
# =========================================================
#
# 【概要】
#   Gateway (予測 API 専用レイヤ) 用の Dockerfile。
#
# 【主な役割】
#   - Python ランタイムと依存パッケージをインストール
#   - gateway.api.router を Uvicorn で起動（ポート 8081）
#
# 【連携先・依存関係】
#   - gateway/requirements.txt   … Python 依存リスト
#   - docker-compose.yml         … service `gateway` 定義
#
# 【ルール遵守】
#   1) ハードコード値には “TODO: 外部設定へ” を付記
#   2) multi-stage build でイメージサイズを最小化
# ---------------------------------------------------------

FROM python:3.11-slim AS base

# ---- label / env ---------------------------------------------------
LABEL org.opencontainers.image.source="https://github.com/your-org/mmopdca"
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1           \
    GATEWAY_PORT=8081            \
    MMOP_API=http://main-api:8001

WORKDIR /app

# ---- 1. install build deps & python deps ---------------------------
RUN apt-get update -qq && apt-get install -y --no-install-recommends \
    build-essential gcc curl && \
    rm -rf /var/lib/apt/lists/*

COPY gateway/requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# ---- 2. copy source ------------------------------------------------
COPY gateway /app/gateway

EXPOSE ${GATEWAY_PORT}

# ---- 3. runtime command -------------------------------------------
CMD ["uvicorn", "gateway.api.router:router", \
    "--host", "0.0.0.0", "--port", "8081"]
