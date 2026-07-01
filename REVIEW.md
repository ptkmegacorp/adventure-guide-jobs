# Review loop — salvage-first pipeline

After every literesearcher run, **`finalize-run.sh` runs automatically** (via `run-next.sh`). Salvage is the primary output path — not an exception.

---

## Default flow (automatic)

```
ON AGENT_RUN_DONE (exit 0):
  RUN ./review-run.sh --run-id {id}        # log review (audit)
  RUN ./extract-findings.sh --run-id {id}  # LR final answer (usually empty)
  RUN ./finalize-run.sh --run-id {id}      # DEFAULT — do not skip
    → salvage-run (re-browse visited URLs + Qwen summarize)
    → update-candidates (findings/master.md + candidates.json)
    → make-run-findings (findings/{run_id}.md)
    → mark findings_saved if salvage substantive
```

Read **`findings/{run_id}-salvage.md`** and **`findings/master.md`** — not the raw log.

---

## Manual commands

```bash
./finalize-run.sh --run-id J3-...           # full pipeline (default after run)
./finalize-run.sh --run-id J3-... --skip-salvage   # re-merge existing salvage only
./salvage-run.sh --run-id J3-...            # salvage only
./update-candidates.sh --from-file findings/J3-...-salvage.md --source-run J3-...
./save-findings.sh --run-id J3-...          # alias for finalize-run.sh
./review-run.sh --run-id J3-...             # log review only
```

---

## What LR vs salvage do

| Stage | Role |
|-------|------|
| **LiteResearcher (8092)** | URL scout — visit seed/candidate careers pages within visit budget |
| **Salvage (8002 + 8093)** | **Primary findings** — re-browse visited URLs, Qwen extracts hiring evidence |
| **review-run (8093 on log)** | Audit only — termination, blocked URLs; do not treat `fail` as no signal if salvage ok |
| **extract-findings** | Audit only — LR final answer; rarely substantive on this stack |

---

## Prompt feedback (when to edit)

Only adjust prompts when **salvage** also returns weak signal:

| Lever | When |
|-------|------|
| **Scope** | LR exceeds visit budget → fewer anchors |
| **Sources** | Salvage shows blocked URLs → swap seed URLs |
| **Seeds** | Wrong candidate set → edit `seeds/` + prompt list |
| **Depth** | Broad J1 fails → skip to regional J2/J3 |

Log edits in [`prompts/CHANGELOG.md`](./CHANGELOG.md).

---

## Outcomes (salvage-based)

| salvage_status | Meaning | Action |
|----------------|---------|--------|
| `ok` | ≥1 employer, summary ≥200 chars | Auto `findings_saved`; master updated |
| `partial` | Some text, thin evidence | Master updated; may retry with `--force` |
| `empty` | No summary | Edit prompt or check browser_server / visited URLs |

LR `review_outcome: fail` with `salvage_status: ok` is **normal** — trust salvage.

---

## Files

```
findings/{run_id}-salvage.md   ← primary employer signal
findings/{run_id}.md           ← per-run rollup (salvage + review + audit)
findings/master.md             ← merged candidate list (from candidates.json)
reviews/{run_id}.md            ← log review (audit)
runs/extracted/{run_id}.md     ← LR final answer (audit)
runs/registry.json             ← salvage/findings/saved state
```
