# 公式イメージに curl を追加
FROM danihodovic/celery-exporter:0.9.1

USER root
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# celery-exporter の実行は nobody ユーザー
USER nobody
# ENTRYPOINT は元イメージのまま (celery-exporter)
