# 公式バイナリから取り出して curl を追加
FROM oliver006/redis_exporter:v1.60.0 AS exporter

FROM alpine:3.19
USER root
RUN apk add --no-cache curl

COPY --from=exporter /redis_exporter /usr/local/bin/redis_exporter
ENTRYPOINT [ "redis_exporter" ]
