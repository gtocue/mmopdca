FROM python:3.11-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

RUN pip install --no-cache-dir --upgrade pip poetry
WORKDIR /app
COPY pyproject.toml poetry.lock ./

RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi \
    --without dev \
    --no-root \
    && poetry run pip install "celery[redis]>=5.4.0"

COPY . .
# entrypoint は compose 側で指定
