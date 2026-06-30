#!/usr/bin/env bash
# Create/refresh a per-run findings file and mark that prompt findings_saved only for substantive final answers.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
RUN_ID=""
PROMPT=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --run-id) RUN_ID="$2"; shift 2 ;;
    --prompt) PROMPT="$2"; shift 2 ;;
    -h|--help) echo "usage: $(basename "$0") [--run-id ID | --prompt J1]"; exit 0 ;;
    *) echo "unknown arg: $1" >&2; exit 1 ;;
  esac
done
if [[ -z "$RUN_ID" && -z "$PROMPT" ]]; then
  echo "usage: $(basename "$0") [--run-id ID | --prompt J1]" >&2
  exit 1
fi
EXTRA_ARGS=()
[[ -n "$RUN_ID" ]] && EXTRA_ARGS+=(--run-id "$RUN_ID")
[[ -n "$PROMPT" ]] && EXTRA_ARGS+=(--prompt "$PROMPT")
EXTRACTED="$($ROOT/lib/extract-findings.py "${EXTRA_ARGS[@]}" --print)"
FINDINGS_PATH="$($ROOT/make-run-findings.sh "${EXTRA_ARGS[@]}")"
ANSWER_CHARS="$(python3 - "$ROOT" "$EXTRACTED" <<'PY'
import re, sys
from pathlib import Path
text=(Path(sys.argv[1])/sys.argv[2]).read_text()
m=re.search(r"- \*\*answer_chars:\*\* (\d+)", text)
print(m.group(1) if m else 0)
PY
)"
if [[ "$ANSWER_CHARS" -ge 100 ]]; then
  PROMPT_ID="$(python3 - "$ROOT" "$EXTRACTED" <<'PY'
import json, sys
from pathlib import Path
root=Path(sys.argv[1]); extracted=sys.argv[2]
reg=json.loads((root/'runs/registry.json').read_text())
for r in reg['runs']:
    if r.get('extracted_path')==extracted:
        print(r['prompt_id']); break
PY
)"
  "$ROOT/run-next.sh" --mark-findings "$PROMPT_ID" >/dev/null
  echo "saved substantive findings: $FINDINGS_PATH"
else
  echo "wrote partial per-run findings (not marked saved): $FINDINGS_PATH"
fi
