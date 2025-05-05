#!/usr/bin/env bash
# =========================================================
# ASSIST_KEY: 【ops/preemptible-wrapper.sh】
# =========================================================
#
# 【概要】
#   Spot／Preemptible VM で SIGTERM を受け取ったとき、
#   “安全にチェックポイントを保存してから” 子プロセスを終了させる
#   ジョブ実行ラッパー。
#
# 【主な役割】
#   1. ENTRYPOINT → 本スクリプトに差し替え、実行コマンドは引数で渡す
#   2. SIGTERM / SIGINT をフックして
#        ・celery worker/beat なら  graceful:shutdown を送る
#        ・任意コマンドなら  pkill -TERM child
#   3. チェックポイント保存のユーザーフックを CALL_CP_HOOK で差し込み可能
#
# 【連携先・依存関係】
#   - core/do/checkpoint.py   … ckpt ディレクトリ仕様を共有
#   - Celery                 … term→warm shutdown で t-ack (= re-queue)
#
# 【ルール】
#   * POSIX sh 互換（busybox, dash でも動く）
#   * child PID を監視し、exit code をそのまま親へ伝搬
# ---------------------------------------------------------

set -euo pipefail

# ───────────────────────────── user-configurable hook
CALL_CP_HOOK="${CALL_CP_HOOK:-}"

# ───────────────────────────── trap handler
_term() {
  echo "[wrapper] caught SIGTERM – start graceful shutdown"

  # 任意チェックポイント保存フック
  if [ -n "${CALL_CP_HOOK}" ] && command -v "${CALL_CP_HOOK%% *}" >/dev/null 2>&1; then
    echo "[wrapper] execute checkpoint hook: ${CALL_CP_HOOK}"
    # shellcheck disable=SC2086
    ${CALL_CP_HOOK} || echo "[wrapper] checkpoint hook failed (ignore)"
  fi

  # Celery worker/beat の場合は control コマンドで優雅に停止
  if [[ "${CMD[0]}" == "celery" ]]; then
    echo "[wrapper] send celery control: shutdown → child ${CHILD_PID}"
    kill -TERM "${CHILD_PID}"
  else
    echo "[wrapper] forward TERM → child ${CHILD_PID}"
    kill -TERM "${CHILD_PID}"
  fi
}

# ───────────────────────────── main
if [ "$#" -lt 1 ]; then
  echo "Usage: $0 <command> [args...]" >&2
  exit 2
fi

# 引数を配列に格納
CMD=("$@")

echo "[wrapper] exec: ${CMD[*]}"
# shellcheck disable=SC2294
"${CMD[@]}" &
CHILD_PID=$!

trap _term TERM INT

# child 終了を待ち、同じ exit code を返す
wait "${CHILD_PID}"
EXIT_CODE=$?
echo "[wrapper] child exited with code ${EXIT_CODE}"
exit "${EXIT_CODE}"
