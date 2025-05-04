#!/bin/sh
set -e

# ───────────────────────────────────────────────────────────────────────────
# init-dsl.sh — prepare DSL + checkpoints dirs, then exec the main command
# ───────────────────────────────────────────────────────────────────────────

echo "[init-dsl] Ensuring DSL directory exists: ${DSL_ROOT}"
mkdir -p "${DSL_ROOT}"
chown -R 1000:1000 "${DSL_ROOT}" 2>/dev/null || true
echo "[init-dsl] DSL directory ready."

echo "[init-dsl] Ensuring checkpoints directory exists: /mnt/checkpoints"
mkdir -p /mnt/checkpoints
chown -R 1000:1000 /mnt/checkpoints 2>/dev/null || true
echo "[init-dsl] Checkpoints directory ready."

# ───────────────────────────────────────────────────────────────────────────
# Finally, hand control over to the container’s CMD (uvicorn / celery / beat)
# ───────────────────────────────────────────────────────────────────────────
exec "$@"
