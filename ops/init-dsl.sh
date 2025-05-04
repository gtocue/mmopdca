#!/usr/bin/env sh
set -e

# ──────────────── 0. DIRS ────────────────
DSL_ROOT="${DSL_ROOT:-/mnt/data/dsl}"
CKPT_ROOT="/mnt/checkpoints"

echo "[init-dsl] Ensuring DSL dir  : ${DSL_ROOT}"
echo "[init-dsl] Ensuring CKPT dir : ${CKPT_ROOT}"
mkdir -p "${DSL_ROOT}" "${CKPT_ROOT}"
# dev 環境では UID=1000 を書込み許可
chown -R 1000:1000 "${DSL_ROOT}" "${CKPT_ROOT}" 2>/dev/null || true
echo "[init-dsl] Dirs ready."

# ──────────────── 1. EXEC ────────────────
echo "[init-dsl] Exec $*"
case "$1" in
  # FastAPI
  uvicorn)
    shift
    exec python -m uvicorn "$@"
    ;;
  # Celery (worker / beat)
  celery)
    shift
    exec python -m celery "$@"
    ;;
  # その他そのまま
  *)
    exec "$@"
    ;;
esac
