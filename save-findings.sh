#!/usr/bin/env bash
# Refresh per-run findings and mark saved when salvage (or LR answer) is substantive.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
RUN_ID=""
PROMPT=""
SKIP_SALVAGE=0
FORCE_SALVAGE=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --run-id) RUN_ID="$2"; shift 2 ;;
    --prompt) PROMPT="$2"; shift 2 ;;
    --skip-salvage) SKIP_SALVAGE=1; shift ;;
    --force-salvage) FORCE_SALVAGE=1; shift ;;
    -h|--help)
      echo "usage: $(basename "$0") [--run-id ID | --prompt J1] [--skip-salvage] [--force-salvage]"
      exit 0
      ;;
    *) echo "unknown arg: $1" >&2; exit 1 ;;
  esac
done
if [[ -z "$RUN_ID" && -n "$PROMPT" ]]; then
  RUN_ID="$(python3 - "$ROOT" "$PROMPT" <<'PY'
import json, sys
from pathlib import Path
root, prompt = Path(sys.argv[1]), sys.argv[2]
reg = json.loads((root / "runs/registry.json").read_text())
matches = [r for r in reg.get("runs", []) if r.get("prompt_id") == prompt and r.get("status") == "completed"]
if not matches:
    raise SystemExit(f"no completed run for {prompt}")
print(sorted(matches, key=lambda r: r.get("started_at", ""))[-1]["run_id"])
PY
)"
fi
if [[ -z "$RUN_ID" ]]; then
  echo "usage: $(basename "$0") [--run-id ID | --prompt J1]" >&2
  exit 1
fi
ARGS=(--run-id "$RUN_ID")
[[ "$SKIP_SALVAGE" -eq 1 ]] && ARGS+=(--skip-salvage)
[[ "$FORCE_SALVAGE" -eq 1 ]] && ARGS+=(--force-salvage)
exec "$ROOT/finalize-run.sh" "${ARGS[@]}"
