#!/usr/bin/env bash
# Run J1 J2 J3 (or custom list) sequentially. Agents: background subagent only — AGENTS.md.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
RUNNER="${ROOT}/run-next.sh"
# shellcheck source=lib/common.sh
source "${ROOT}/lib/common.sh"

usage() {
  cat <<EOF
usage: $(basename "$0") [OPTIONS] [J1 [J2 ...]]

Default: J1 J2 J3 J4 (skips prompts already complete unless --force)

Options:
  --force    Re-run even if findings already saved
  --status   Show registry and exit

Examples:
  $(basename "$0")                    # J1 → J2 → J3 → J4 (skip completed)
  $(basename "$0") --force J1 J2 J3 J4   # full batch with new seed picks
EOF
}

FORCE=0
if [[ "${1:-}" == "--status" ]]; then
  registry_status
  exit 0
fi
if [[ "${1:-}" == "--force" ]]; then
  FORCE=1
  shift
fi
if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

PROMPTS=("$@")
if [[ ${#PROMPTS[@]} -eq 0 ]]; then
  PROMPTS=(J1 J2 J3 J4)
fi

echo "Batch plan: ${PROMPTS[*]}"
registry_status
echo

for id in "${PROMPTS[@]}"; do
  case "$id" in
    J1|J2|J3|J4) ;;
    *) echo "unknown prompt id: $id" >&2; exit 1 ;;
  esac
done

if [[ -x "${ROOT}/apply-seed-batch.sh" ]]; then
  echo "Applying active seed batch before batch run..."
  "${ROOT}/apply-seed-batch.sh"
fi

for i in "${!PROMPTS[@]}"; do
  id="${PROMPTS[$i]}"
  echo "========== [$((i + 1))/${#PROMPTS[@]}] ${id} =========="
  if [[ "$FORCE" -eq 1 ]]; then
    "${RUNNER}" --force "$id" || true
  else
    "${RUNNER}" "$id" || true
  fi
  echo
done

echo "Batch complete: ${PROMPTS[*]}"
echo "AGENT_BATCH_DONE {\"prompts\":\"${PROMPTS[*]}\"}"
registry_status
echo "Primary output: findings/*-salvage.md and findings/master.md (auto via finalize-run)"
