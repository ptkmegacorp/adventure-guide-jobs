# Findings

Per-run and merged employer findings.

| File | Role |
|------|------|
| `{run_id}-salvage.md` | **Primary signal** — re-browsed URLs + Qwen summary (auto after every run) |
| `{run_id}.md` | Per-run rollup (salvage + review + LR audit) |
| `master.md` | Merged deduped list (auto from salvage via `update-candidates.sh`) |
| `candidates.json` | Structured candidate DB backing `master.md` |
| `legacy.md` | Old single-file archive |

Raw logs are evidence. Salvage is conclusions. LR final answer is usually empty on this stack.
