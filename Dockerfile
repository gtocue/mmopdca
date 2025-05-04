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
# └───────────────★ ここが決定打

# ---- アプリコード -------------------------------------------------
COPY . .

# init-dsl エントリ
COPY ops/init-dsl.sh /usr/local/bin/docker-entrypoint-init-dsl.sh
RUN dos2unix /usr/local/bin/docker-entrypoint-init-dsl.sh \
    && chmod +x /usr/local/bin/docker-entrypoint-init-dsl.sh
