#!/usr/bin/env bash
# Review latest (or specific) run — sidecar summary + registry update.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
PY="${ROOT}/lib/review-run.py"

usage() {
  cat <<EOF
usage: $(basename "$0") --prompt J1 [--no-sidecar]
       $(basename "$0") --run-id J1-20260630-171457
       $(basename "$0") --log runs/2026-06-30-171448-J1.log

Uses Qwen3.5-4B sidecar (:8093) when up; extractive fallback otherwise.
Writes reviews/{run_id}.md and updates runs/registry.json.
EOF
}

[[ $# -eq 0 ]] && { usage; exit 1; }
python3 "$PY" "$@"
