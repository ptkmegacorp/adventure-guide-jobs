#!/usr/bin/env bash
# Run one prompt, write per-run findings, and notify the active Pi agent via pi-agent-notify.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
NOTIFY="${PI_AGENT_NOTIFY_BIN:-$HOME/.pi/agent/bin/pi-agent-notify}"
PROMPT_ID="${1:-}"
FORCE=0
if [[ "${PROMPT_ID}" == "--force" ]]; then
  FORCE=1
  PROMPT_ID="${2:-}"
fi
if [[ -z "$PROMPT_ID" || "$PROMPT_ID" == "-h" || "$PROMPT_ID" == "--help" ]]; then
  echo "usage: $(basename "$0") [--force] J1|J2|J3|J4" >&2
  exit 1
fi
case "$PROMPT_ID" in J1|J2|J3|J4) ;; *) echo "unknown prompt id: $PROMPT_ID" >&2; exit 1 ;; esac

TMP="$(mktemp /tmp/adventure-${PROMPT_ID}-XXXX.log)"
cleanup() { rm -f "$TMP"; }
trap cleanup EXIT

cd "$ROOT"
if [[ "$FORCE" -eq 1 ]]; then
  ./run-next.sh --force "$PROMPT_ID" 2>&1 | tee "$TMP"
else
  ./run-next.sh "$PROMPT_ID" 2>&1 | tee "$TMP"
fi

DONE_JSON="$(grep 'AGENT_RUN_DONE' "$TMP" | tail -1 | sed 's/^.*AGENT_RUN_DONE //')"
if [[ -z "$DONE_JSON" ]]; then
  MSG="${PROMPT_ID} finished but AGENT_RUN_DONE was not found. Check $TMP and ./driver-status.sh"
  [[ -x "$NOTIFY" ]] && "$NOTIFY" --title "Adventure Guide Jobs" --severity warning "$MSG" || true
  echo "$MSG" >&2
  exit 2
fi

RUN_ID="$(python3 - <<'PY' "$DONE_JSON"
import json, sys
print(json.loads(sys.argv[1]).get('run_id',''))
PY
)"
EXIT_CODE="$(python3 - <<'PY' "$DONE_JSON"
import json, sys
print(json.loads(sys.argv[1]).get('exit_code',''))
PY
)"

if [[ -n "$RUN_ID" && "$EXIT_CODE" == "0" ]]; then
  SAVE_OUT="$(./save-findings.sh --run-id "$RUN_ID" 2>&1 || true)"
  STATUS="$(./driver-status.sh | tail -20)"
  MSG="${PROMPT_ID} completed: ${RUN_ID}

${SAVE_OUT}

${STATUS}"
  [[ -x "$NOTIFY" ]] && printf '%s' "$MSG" | "$NOTIFY" --title "Adventure Guide Jobs" || true
  printf '%s\n' "$MSG"
else
  MSG="${PROMPT_ID} failed or had no run_id. exit_code=${EXIT_CODE}. Run ./driver-status.sh"
  [[ -x "$NOTIFY" ]] && "$NOTIFY" --title "Adventure Guide Jobs" --severity warning "$MSG" || true
  echo "$MSG" >&2
  exit 3
fi
