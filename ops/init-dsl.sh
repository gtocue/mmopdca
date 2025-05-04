###############################################################################
# ASSIST_KEY: 【ops/init-dsl.sh】           ← ファイル先頭ヘッダは必ず残すこと
#   DSL と Checkpoints の両ディレクトリを確実に作成したうえで、
#   受け取った引数（CMD）を実行する共通エントリポイント。
#
#   ● API コンテナ       … CMD ["uvicorn",  "api.main_api:app", ...]
#   ● Worker / Beat … CMD ["celery",   "-A", "core.celery_app:celery_app", ...]
#
#   Alpine slim 系で発生する “uvicorn: not found” 問題を回避するため、
#   先頭引数が `uvicorn` の場合は **python -m uvicorn** へ置き換えて実行する。
###############################################################################
#!/usr/bin/env sh
set -e

# ────────────────────────────────
# 0. 変数
# ────────────────────────────────
DSL_ROOT="${DSL_ROOT:-/mnt/data/dsl}"
CKPT_ROOT="/mnt/checkpoints"

# ────────────────────────────────
# 1. DSL / Checkpoints フォルダ整備
# ────────────────────────────────
echo "[init-dsl] Ensuring DSL directory exists: ${DSL_ROOT}"
mkdir -p "${DSL_ROOT}"
# ※ dev モードで 1000:1000 を使う場合のみ chown
chown -R 1000:1000 "${DSL_ROOT}" 2>/dev/null || true
echo "[init-dsl] DSL directory ready."

echo "[init-dsl] Ensuring checkpoints directory exists: ${CKPT_ROOT}"
mkdir -p "${CKPT_ROOT}"
chown -R 1000:1000 "${CKPT_ROOT}" 2>/dev/null || true
echo "[init-dsl] Checkpoints directory ready."

# ────────────────────────────────
# 2. CMD を実行
#    uvicorn だけ python -m で呼び出す
# ────────────────────────────────
echo "[init-dsl] Exec $*"
case "$1" in
  uvicorn)
    shift               # 先頭 (uvicorn) を削除
    exec python -m uvicorn "$@"
    ;;
  *)
    exec "$@"
    ;;
esac
