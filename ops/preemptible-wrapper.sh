#!/usr/bin/env bash
# =========================================================
# ASSIST_KEY: 縲塵ps/preemptible-wrapper.sh縲・# =========================================================
#
# 縲先ｦりｦ√・#   Spot・襲reemptible VM 縺ｧ SIGTERM 繧貞女縺大叙縺｣縺溘→縺阪・#   窶懷ｮ牙・縺ｫ繝√ぉ繝・け繝昴う繝ｳ繝医ｒ菫晏ｭ倥＠縺ｦ縺九ｉ窶・蟄舌・繝ｭ繧ｻ繧ｹ繧堤ｵゆｺ・＆縺帙ｋ
#   繧ｸ繝ｧ繝門ｮ溯｡後Λ繝・ヱ繝ｼ縲・#
# 縲蝉ｸｻ縺ｪ蠖ｹ蜑ｲ縲・#   1. ENTRYPOINT 竊・譛ｬ繧ｹ繧ｯ繝ｪ繝励ヨ縺ｫ蟾ｮ縺玲崛縺医∝ｮ溯｡後さ繝槭Φ繝峨・蠑墓焚縺ｧ貂｡縺・#   2. SIGTERM / SIGINT 繧偵ヵ繝・け縺励※
#        繝ｻcelery worker/beat 縺ｪ繧・ graceful:shutdown 繧帝√ｋ
#        繝ｻ莉ｻ諢上さ繝槭Φ繝峨↑繧・ pkill -TERM child
#   3. 繝√ぉ繝・け繝昴う繝ｳ繝井ｿ晏ｭ倥・繝ｦ繝ｼ繧ｶ繝ｼ繝輔ャ繧ｯ繧・CALL_CP_HOOK 縺ｧ蟾ｮ縺苓ｾｼ縺ｿ蜿ｯ閭ｽ
#
# 縲宣｣謳ｺ蜈医・萓晏ｭ倬未菫ゅ・#   - core/do/checkpoint.py   窶ｦ ckpt 繝・ぅ繝ｬ繧ｯ繝医Μ莉墓ｧ倥ｒ蜈ｱ譛・#   - Celery                 窶ｦ term竊蜘arm shutdown 縺ｧ t-ack (= re-queue)
#
# 縲舌Ν繝ｼ繝ｫ縲・#   * POSIX sh 莠呈鋤・・usybox, dash 縺ｧ繧ょ虚縺擾ｼ・#   * child PID 繧堤屮隕悶＠縲‘xit code 繧偵◎縺ｮ縺ｾ縺ｾ隕ｪ縺ｸ莨晄成
# ---------------------------------------------------------

set -euo pipefail

# 笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏 user-configurable hook
CALL_CP_HOOK="${CALL_CP_HOOK:-}"

# 笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏 trap handler
_term() {
  echo "[wrapper] caught SIGTERM 窶・start graceful shutdown"

  # 莉ｻ諢上メ繧ｧ繝・け繝昴う繝ｳ繝井ｿ晏ｭ倥ヵ繝・け
  if [ -n "${CALL_CP_HOOK}" ] && command -v "${CALL_CP_HOOK%% *}" >/dev/null 2>&1; then
    echo "[wrapper] execute checkpoint hook: ${CALL_CP_HOOK}"
    # shellcheck disable=SC2086
    ${CALL_CP_HOOK} || echo "[wrapper] checkpoint hook failed (ignore)"
  fi

  # Celery worker/beat 縺ｮ蝣ｴ蜷医・ control 繧ｳ繝槭Φ繝峨〒蜆ｪ髮・↓蛛懈ｭ｢
  if [[ "${CMD[0]}" == "celery" ]]; then
    echo "[wrapper] send celery control: shutdown 竊・child ${CHILD_PID}"
    kill -TERM "${CHILD_PID}"
  else
    echo "[wrapper] forward TERM 竊・child ${CHILD_PID}"
    kill -TERM "${CHILD_PID}"
  fi
}

# 笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏 main
if [ "$#" -lt 1 ]; then
  echo "Usage: $0 <command> [args...]" >&2
  exit 2
fi

# 蠑墓焚繧帝・蛻励↓譬ｼ邏・CMD=("$@")

echo "[wrapper] exec: ${CMD[*]}"
# shellcheck disable=SC2294
"${CMD[@]}" &
CHILD_PID=$!

trap _term TERM INT

# child 邨ゆｺ・ｒ蠕・■縲∝酔縺・exit code 繧定ｿ斐☆
wait "${CHILD_PID}"
EXIT_CODE=$?
echo "[wrapper] child exited with code ${EXIT_CODE}"
exit "${EXIT_CODE}"

