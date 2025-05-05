#!/usr/bin/env sh
set -eu

###############################################################################
# init-dsl.sh
# ─────────────────────────────────────────────────────────────────────────────
# ・DSL ディレクトリ（モデル／DSL ファイル）とチェックポイント用ディレクトリを
#   必ず用意してからアプリ本体を起動するエントリポイント。
# ・開発環境では UID=1000 / GID=1000 が書き込めるよう chown する。
###############################################################################

# ────────────────────────────── 0. DIRS ──────────────────────────────
DSL_ROOT="${DSL_ROOT:-/mnt/data/dsl}"
CKPT_ROOT="${CKPT_ROOT:-/mnt/checkpoints}"

echo "[init-dsl] Ensuring DSL dir  : ${DSL_ROOT}"
echo "[init-dsl] Ensuring CKPT dir : ${CKPT_ROOT}"
mkdir -p "${DSL_ROOT}" "${CKPT_ROOT}"

# 開発環境（Docker Desktop / docker compose）では　UID 1000 が動かすため所有権を譲る
# 失敗しても（本番 root 実行など）無視して続行
chown -R 1000:1000 "${DSL_ROOT}" "${CKPT_ROOT}" 2>/dev/null || true
echo "[init-dsl] Dirs ready."

# ────────────────────────────── 1. EXEC ──────────────────────────────
echo "[init-dsl] Exec $*"
case "$1" in
  # ---------- FastAPI ----------
  uvicorn)
    shift
    exec python -m uvicorn "$@"
    ;;

  # ---------- Celery (worker / beat) ----------
  celery)
    shift
    exec celery "$@"
    ;;

  # ---------- その他そのまま ----------
  *)
    exec "$@"
    ;;
esac
