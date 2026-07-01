#!/usr/bin/env bash
# Concise deterministic status for the main driver (salvage-first pipeline).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
python3 - "$ROOT" <<'PY'
import json, sys
from pathlib import Path
root = Path(sys.argv[1])
reg = json.loads((root / "runs/registry.json").read_text())
runs = reg.get("runs", [])
print("# Adventure Guide Jobs status\n")
running = [r for r in runs if r.get("status") == "running"]
print("Active run:", ", ".join(r["run_id"] for r in running) if running else "none")
print("\n## Prompts")
for pid in ["J1", "J2", "J3", "J4"]:
    ps = reg.get("prompts", {}).get(pid, {})
    print(
        f"- {pid}: {ps.get('status', 'pending')} | "
        f"salvage={ps.get('last_salvage_status', '—')} ({ps.get('salvage_employer_count', '—')} employers) | "
        f"findings={ps.get('last_findings', '—')}"
    )
recent = sorted(
    [r for r in runs if r.get("status") == "completed"],
    key=lambda x: x.get("started_at", ""),
    reverse=True,
)[:5]
print("\n## Recent completed runs")
if recent:
    for r in recent:
        print(
            f"- {r['run_id']} ({r['prompt_id']}): "
            f"salvage={r.get('salvage_status', '—')} employers={r.get('salvage_employer_count', '—')} "
            f"saved={'yes' if r.get('findings_saved') else 'no'} "
            f"master={'updated' if r.get('salvage_status') in ('ok', 'partial') else '—'}"
        )
else:
    print("- none")
print("\n## Recommended next")
if running:
    print("Wait for active run to finish.")
else:
    order = ["J1", "J2", "J3", "J4"]
    pending = [
        p
        for p in order
        if reg.get("prompts", {}).get(p, {}).get("status", "pending") not in ("findings_saved", "done")
    ]
    if pending:
        print(f"./run-next.sh {pending[0]}   # LR scouts URLs; finalize-run salvages by default")
    else:
        print("All prompts findings_saved. Review findings/master.md or ./run-next.sh --force J* to retry.")
    unsalvaged = [
        r
        for r in runs
        if r.get("status") == "completed" and not r.get("salvage_path")
    ]
    if unsalvaged:
        r = unsalvaged[-1]
        print(f"./finalize-run.sh --run-id {r['run_id']}   # backfill salvage for older run")
PY
