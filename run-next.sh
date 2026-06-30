#!/usr/bin/env bash
# Run one adventure-guide-jobs research prompt via LiteResearcher.
# Agents: launch via background subagent or Shell(block_until_ms=0) — see AGENTS.md.
# Emits AGENT_RUN_START / AGENT_RUN_DONE for completion handling.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
LR_APP="/home/bot/projects/literesearcher-app"
RUNS_DIR="${ROOT}/runs"
# shellcheck source=lib/common.sh
source "${ROOT}/lib/common.sh"

usage() {
  cat <<EOF
usage: $(basename "$0") [OPTIONS] [PROMPT_ID]

PROMPT_ID: J1 J2 J3 J4  (default: next pending from runs/registry.json)

Options:
  --dry-run           Print prompt only
  --force             Run even if prompt already completed in registry
  --status            Show run registry and exit
  --mark-findings ID  Mark prompt findings saved (updates registry + research-prompts.md)

Examples:
  $(basename "$0")                  # next pending prompt
  $(basename "$0") J2               # specific prompt
  $(basename "$0") --mark-findings J1
  $(basename "$0") --status
EOF
}

DRY_RUN=0
FORCE=0
MARK_FINDINGS=""
PROMPT_ID=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help) usage; exit 0 ;;
    --dry-run) DRY_RUN=1; shift ;;
    --force) FORCE=1; shift ;;
    --status) registry_status; exit 0 ;;
    --mark-findings)
      MARK_FINDINGS="$2"
      shift 2
      ;;
    J1|J2|J3|J4) PROMPT_ID="$1"; shift ;;
    *) echo "unknown arg: $1" >&2; usage; exit 1 ;;
  esac
done

if [[ -n "$MARK_FINDINGS" ]]; then
  registry_mark_findings "$MARK_FINDINGS"
  echo "Registry + research-prompts.md updated for ${MARK_FINDINGS}"
  registry_status
  exit 0
fi

resolve_prompt_id() {
  if [[ -n "$PROMPT_ID" ]]; then
    echo "$PROMPT_ID"
    return
  fi
  local nxt
  nxt="$(registry_next)"
  if [[ -n "$nxt" ]]; then
    echo "$nxt"
    return
  fi
  echo "J1"
}

PROMPT_ID="$(resolve_prompt_id)"
PROMPT_FILE="$(resolve_prompt_file "$PROMPT_ID")"

if [[ -z "$PROMPT_FILE" || ! -f "$PROMPT_FILE" ]]; then
  echo "ERROR: no prompt file for ${PROMPT_ID} in ${ROOT}/prompts/" >&2
  exit 1
fi

if [[ "$FORCE" -eq 0 ]] && registry_is_complete "$PROMPT_ID"; then
  echo "SKIP: ${PROMPT_ID} already complete in runs/registry.json (findings saved)."
  echo "Use --force to re-run, or ./run-status.sh to see history."
  registry_status
  exit 0
fi

if registry_any_running; then
  echo "SKIP: another research run is already marked running in runs/registry.json."
  echo "Do not start a second LiteResearcher/GPU job; wait for the active run to finish."
  registry_status
  exit 2
fi

QUESTION="$(tr '\n' ' ' < "$PROMPT_FILE" | sed 's/  */ /g')"

if [[ "$DRY_RUN" -eq 1 ]]; then
  echo "=== PROMPT ${PROMPT_ID} (${PROMPT_FILE}) ==="
  cat "$PROMPT_FILE"
  registry_status
  exit 0
fi

mkdir -p "$RUNS_DIR"
STAMP="$(date +%Y-%m-%d-%H%M%S)"
LOG="${RUNS_DIR}/${STAMP}-${PROMPT_ID}.log"
REL_LOG="runs/${STAMP}-${PROMPT_ID}.log"

if ! lr_ready; then
  echo "Starting LiteResearcher stack (stops Pig :8091)..."
  "${LR_APP}/scripts/start-all.sh"
else
  echo "LiteResearcher stack already up."
fi

RUN_ID="$(registry_start "$PROMPT_ID" "$REL_LOG" "$PROMPT_FILE")"
echo "Registry run_id=${RUN_ID}"
echo "AGENT_RUN_START {\"prompt\":\"${PROMPT_ID}\",\"run_id\":\"${RUN_ID}\",\"log\":\"${REL_LOG}\"}"
echo "Running ${PROMPT_ID} → ${LOG}"

set +e
{
  echo "# LiteResearcher run: ${PROMPT_ID}"
  echo "# run_id: ${RUN_ID}"
  echo "# Started: $(date -Iseconds)"
  echo "# Prompt file: ${PROMPT_FILE}"
  echo "---"
  echo
  "${LR_APP}/scripts/smoke-test.sh" "$QUESTION"
} 2>&1 | tee "$LOG"
EXIT_CODE=${PIPESTATUS[0]}
set -e

registry_finish "$RUN_ID" "$EXIT_CODE"

echo "AGENT_RUN_REVIEW {\"prompt\":\"${PROMPT_ID}\",\"run_id\":\"${RUN_ID}\",\"log\":\"${REL_LOG}\"}"
if [[ -x "${ROOT}/review-run.sh" ]]; then
  "${ROOT}/review-run.sh" --run-id "$RUN_ID" 2>/dev/null || \
    "${ROOT}/review-run.sh" --run-id "$RUN_ID" --no-sidecar 2>/dev/null || \
    echo "WARN: review-run failed (see REVIEW.md)"
fi

echo "AGENT_RUN_DONE {\"prompt\":\"${PROMPT_ID}\",\"run_id\":\"${RUN_ID}\",\"exit_code\":${EXIT_CODE},\"log\":\"${REL_LOG}\"}"
echo
if [[ "$EXIT_CODE" -eq 0 ]]; then
  echo "Done (${RUN_ID}). Next steps:"
  echo "  1. Review ${LOG}"
  echo "  2. Copy table → ${ROOT}/findings.md"
  echo "  3. ./run-next.sh --mark-findings ${PROMPT_ID}"
else
  echo "Run failed (exit ${EXIT_CODE}). Registry updated; retry with: ./run-next.sh ${PROMPT_ID}"
fi
registry_status
