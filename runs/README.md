# Run logs

Raw LiteResearcher output from `./run-next.sh` and `./run-batch.sh`.

## How runs are launched

| Who | How |
|-----|-----|
| **Cursor agent** | Background **Task subagent** or `Shell(block_until_ms=0)` — see [`AGENTS.md`](../AGENTS.md) |
| **Human** | Foreground in terminal: `./run-next.sh J1` |

Agents must **not** foreground-run these scripts with manual poll timers. Wait for shell/subagent completion + `AGENT_RUN_DONE`.

## Registry

**[`registry.json`](./registry.json)** — loop state (`pending` → `running` → `run_done` → `findings_saved`).

```bash
../run-status.sh
```

## Completion sentinels

Scripts print JSON lines for the worker to parse:

```
AGENT_RUN_START {"prompt":"J1","run_id":"...","log":"runs/..."}
AGENT_RUN_DONE  {"prompt":"J1","run_id":"...","exit_code":0,"log":"runs/..."}
```

On `exit_code: 0` → read `log` → append table to `../findings.md` → `../run-next.sh --mark-findings J1`

## Log files

`YYYY-MM-DD-HHMMSS-J*.log` — immutable. Re-runs append new registry entries; do not delete old logs.
