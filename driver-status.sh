#!/usr/bin/env bash
# Concise deterministic status for the main driver.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
python3 - "$ROOT" <<'PY'
import json, sys
from pathlib import Path
root=Path(sys.argv[1]); reg=json.loads((root/'runs/registry.json').read_text())
runs=reg.get('runs', [])
print('# Adventure Guide Jobs status\n')
running=[r for r in runs if r.get('status')=='running']
print('Active run:', ', '.join(r['run_id'] for r in running) if running else 'none')
print('\n## Prompts')
for pid in ['J1','J2','J3','J4']:
    ps=reg.get('prompts',{}).get(pid,{})
    print(f"- {pid}: {ps.get('status','pending')} | last_log={ps.get('last_log','—')} | extracted={ps.get('last_extracted','—')} | findings={ps.get('last_findings','—')} | extraction={ps.get('last_extraction_status','—')}")
ready=[r for r in runs if r.get('status')=='completed' and not r.get('findings_saved')]
print('\n## Ready unsaved completed runs')
if ready:
    for r in sorted(ready, key=lambda x:x.get('started_at','')):
        print(f"- {r['run_id']} ({r['prompt_id']}): findings={r.get('findings_path','no')} extracted={r.get('extracted_path','no')} extraction={r.get('extraction_status','—')} chars={r.get('answer_chars','—')} review={r.get('review_outcome','—')} log={r.get('log')}")
else:
    print('- none')
print('\n## Recommended next')
if running:
    print('Wait for active run to finish.')
elif ready:
    r=ready[-1]
    if not r.get('findings_path'):
        print(f"./save-findings.sh --run-id {r['run_id']}  # writes per-run findings; marks saved only if substantive")
    elif r.get('extraction_status') == 'no_final_answer':
        print(f"Partial findings exist at {r.get('findings_path')}; retry/tighten or skip to next prompt.")
    elif r.get('extracted_path'):
        print(f"./save-findings.sh --run-id {r['run_id']}")
    else:
        print(f"./extract-findings.sh --run-id {r['run_id']}")
else:
    order=['J1','J2','J3','J4']
    nxt=next((p for p in order if reg.get('prompts',{}).get(p,{}).get('status','pending') not in ('findings_saved','done')), None)
    print(f"./run-next.sh {nxt}" if nxt else 'All prompts saved; consolidate.')
PY
