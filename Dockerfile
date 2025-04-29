# -------------------------------------------------
# Dockerfile          – Celery Worker / Beat 共通
# -------------------------------------------------
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# ----- install Poetry -----
RUN pip install --no-cache-dir --upgrade pip poetry

WORKDIR /app
COPY pyproject.toml poetry.lock ./

# ----- ここがビルドの核心 -----
RUN poetry config virtualenvs.create false \
    && poetry lock                          \ 
    && poetry install --no-interaction --no-ansi \
    --without dev --no-root            \  
    && poetry run pip install "celery[redis]>=5.4.0"

# 残りのソース
COPY . .

# ENTRYPOINT / CMD は docker-compose.yml で上書き
