# Workflow example — salvage-first research loop

LiteResearcher scouts URLs; **salvage produces the findings**. This is automatic after every `./run-next.sh` run.

## Normal loop

```bash
cd /home/bot/adventure-guide-jobs
./driver-status.sh
```

If no run is active, start the next prompt in the background (see `AGENTS.md`):

```bash
./run-next.sh J3
# or
./run-and-save-notify.sh --force J3
```

`run-next.sh` will:

1. register the run in `runs/registry.json`
2. run LiteResearcher (URL scout)
3. write the raw log in `runs/`
4. run `review-run.sh` (log audit)
5. run `extract-findings.sh` (LR final answer audit)
6. run **`finalize-run.sh`** (salvage → update-candidates → per-run findings → mark saved)

## After a run finishes

```bash
./driver-status.sh
```

Check:

- `findings/{run_id}-salvage.md` — **primary signal**
- `findings/master.md` — merged employers
- `findings/{run_id}.md` — per-run rollup

No manual salvage step needed unless backfilling an older run:

```bash
./finalize-run.sh --run-id RUN_ID
```

## Division of responsibility

| Component | Job |
|-----------|-----|
| LR-4B `:8092` | Pick and visit seed/candidate URLs |
| browser_server `:8002` + Qwen `:8093` | Re-browse + summarize (salvage) |
| `finalize-run.sh` | Default post-run pipeline |
| `driver-status.sh` | What to run next |
| Main agent | Read salvage/master; edit prompts only when salvage is weak |

## Registry states

- `pending` — not completed
- `running` — active LR job
- `run_done` — LR finished; finalize pending or partial
- `findings_saved` — salvage (or LR answer) substantive; skip unless `--force`

Success = **`salvage_status: ok`** and rows in `findings/master.md`, not LR final answer.
