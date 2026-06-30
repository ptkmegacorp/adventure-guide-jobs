#!/usr/bin/env bash
# Shared helpers for adventure-guide-jobs run scripts.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REGISTRY_PY="${ROOT}/lib/run-registry.py"

registry_status() {
  python3 "$REGISTRY_PY" status
}

registry_next() {
  python3 "$REGISTRY_PY" next
}

registry_is_complete() {
  local prompt_id="$1"
  [[ "$(python3 "$REGISTRY_PY" is-complete "$prompt_id")" == "yes" ]]
}

registry_any_running() {
  [[ "$(python3 "$REGISTRY_PY" any-running)" == "yes" ]]
}

registry_start() {
  python3 "$REGISTRY_PY" start "$1" "$2" "$3"
}

registry_finish() {
  python3 "$REGISTRY_PY" finish "$1" "$2"
}

registry_mark_findings() {
  local prompt_id="$1"
  local log_path="${2:-}"
  if [[ -n "$log_path" ]]; then
    python3 "$REGISTRY_PY" complete "$prompt_id" "$log_path"
  else
    python3 "$REGISTRY_PY" complete "$prompt_id"
  fi
}

resolve_prompt_file() {
  local prompt_id="$1"
  ls "${ROOT}/prompts/${prompt_id}-"*.txt 2>/dev/null | head -1
}

lr_ready() {
  curl -sf http://127.0.0.1:8092/health >/dev/null 2>&1 \
    && curl -sf http://127.0.0.1:8093/health >/dev/null 2>&1 \
    && curl -sf http://127.0.0.1:8001/health >/dev/null 2>&1 \
    && curl -sf http://127.0.0.1:8002/health >/dev/null 2>&1
}
