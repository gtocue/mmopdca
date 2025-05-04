#!/usr/bin/env sh
set -e

# ──────────────── 0. VARIABLES ────────────────
DSL_ROOT="${DSL_ROOT:-/mnt/data/dsl}"
CKPT_ROOT="/mnt/checkpoints"

# ──────────────── 1. PREPARE DIRS ─────────────
echo "[init-dsl] Ensuring DSL dir  : $DSL_ROOT"
mkdir -p  "$DSL_ROOT"        && chown -R 1000:1000 "$DSL_ROOT"  || true
echo "[init-dsl] Ensuring CKPT dir : $CKPT_ROOT"
mkdir -p  "$CKPT_ROOT"       && chown -R 1000:1000 "$CKPT_ROOT" || true
echo "[init-dsl] Dirs ready."

# ──────────────── 2. EXEC CMD ─────────────────
echo "[init-dsl] Exec $*"

# 1st token を python -m に置換するだけで済む
case "$1" in
  uvicorn)
    shift
    exec python -m uvicorn "$@"
    ;;
  celery)
    shift
    exec python -m celery "$@"
    ;;
  *)
    exec "$@"
    ;;
esac
