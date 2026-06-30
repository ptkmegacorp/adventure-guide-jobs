# Execution plan: J1 → J2 → J3

Run the first three job-discovery prompts via LiteResearcher. Goal: a deduplicated employer list in `findings.md` covering **global breadth (J1)**, **NZ driver-guides (J2)**, and **USA/Canada field instructors (J3)**.

J4 (Norway) is out of scope for this batch — run separately after reviewing J1–J3 results.

---

## Why this order

| Step | Prompt | Purpose | Overlap with prior |
|------|--------|---------|-------------------|
| 1 | **J1** | Cast a wide net — 20+ employers across NZ, USA, Canada, Norway | — |
| 2 | **J2** | Deepen NZ driver-guide / trip leader listings (Workabout, operator careers) | May repeat J1 NZ rows — **merge, don't duplicate** |
| 3 | **J3** | Deepen USA/Canada program leaders (Pacific Discovery–like) | May repeat J1 US/CA rows — **merge, enrich** |

J1 first gives context; J2/J3 fill gaps J1 missed in their regions.

---

## Pre-flight (once, before J1)

- [ ] **Check registry** — `./run-status.sh` (skip prompts already `findings_saved`)
- [ ] **GPU free enough** — LiteResearcher needs ~8–9 GB VRAM (LR-4B + Qwen3.5-4B on CUDA0). Pig `:8091` will stop; that's fine.
- [ ] **Qwen summary GGUF present** — `/home/bot/models/Qwen_Qwen3.5-4B-Q4_K_M.gguf`
- [ ] **SearXNG up** — `curl -sf 'http://127.0.0.1:8888/search?q=ping&format=json'` (pig-searxng container is OK)
- [ ] **Preview prompts** (optional):

```bash
cd /home/bot/adventure-guide-jobs
./run-next.sh --dry-run J1
./run-next.sh --dry-run J2
./run-next.sh --dry-run J3
```

**Time budget:** ~15–25 minutes per prompt. Total batch ~1–1.5 hours.

---

## Execution (agents: background subagent only)

**Do not** run `./run-batch.sh` in the foreground with long Await timers.

```
Parent agent:
  Task(generalPurpose, run_in_background=true):
    "Run /home/bot/adventure-guide-jobs/run-batch.sh (or run-next.sh J1).
     On AGENT_RUN_DONE: copy table to findings.md, --mark-findings, report status."
  Wait for subagent completion notification — not manual polling.
```

Subagent prompt template: [`AGENTS.md`](./AGENTS.md#subagent-prompt-template-copy-paste)

### Humans — direct terminal

```bash
cd /home/bot/adventure-guide-jobs
./run-batch.sh J1 J2 J3
```

---

## After each run

1. **Open the log** — path in `./run-status.sh` (`last_log` for that prompt) or newest `runs/*-J*.log`.
2. **Find the final answer** — section after `prediction:` or the last markdown table.
3. **Copy the table** into `findings.md` (include `run_id` from log header if present).
4. **Mark in registry:**

```bash
./run-next.sh --mark-findings J1   # updates runs/registry.json + checks off research-prompts.md
```

5. **Verify:** `./run-status.sh` should show `findings_saved` for that prompt.

---

## Consolidation (after J3)

Merge all three runs into one view at the top of `findings.md`:

### Deduplication rules

- Same company in J1 and J2/J3 → **one row**, keep the richest careers URL and hiring signal.
- Prefer **live posting** > **seasonal recruiter** > **careers page only**.
- Tag each row: `source: J1 | J2 | J3`.

### Summary table to add

After merging, add a **Master list** section:

| Company | Region | Role type | Careers URL | Hiring signal | Fit | Sources |
|---------|--------|-----------|-------------|---------------|-----|---------|

**Fit** (your taxonomy): High / Medium / Low / Future — see `README.md`.

### Success criteria

- [ ] **≥20 unique employers** in master list (J1 should contribute most)
- [ ] **≥8 NZ** entries with driver-guide or trip leader signal (J2 boost)
- [ ] **≥10 USA/Canada** field instructor / program leader entries (J3 boost)
- [ ] **Zero Indeed URLs** in findings (if any slipped in, delete those rows)
- [ ] Every High/Medium fit row has a **direct careers or apply URL**

---

## If a run fails

| Symptom | Action |
|---------|--------|
| `8092 down` / stack not ready | `projects/literesearcher-app/scripts/start-all.sh`, retry |
| Timeout / no tool calls | Re-run same prompt; LR occasionally stops early |
| Mostly Indeed results | Re-run with `--dry-run` to confirm prompt; check log for `indeed.com` visits |
| JSON summary warnings in browser log | OK if fallback worked; check if visits returned content |
| OOM on GPU | Reduce LR ctx in `literesearcher-app/config/.env` (`MAIN_MAX_MODEL_LEN=8192`), restart stack |

---

## Checklist (printable)

```
Phase 1 — J1 broad discovery
[ ] ./run-status.sh
[ ] ./run-batch.sh J1  OR  ./run-next.sh J1
[ ] copy table → findings.md
[ ] ./run-next.sh --mark-findings J1

Phase 2 — J2 NZ driver-guides
[ ] ./run-next.sh J2          (auto-skips if already findings_saved)
[ ] merge NZ rows in findings.md
[ ] ./run-next.sh --mark-findings J2

Phase 3 — J3 USA/Canada field instructors
[ ] ./run-next.sh J3
[ ] merge US/CA rows
[ ] ./run-next.sh --mark-findings J3

Phase 4 — consolidate
[ ] ./run-status.sh shows J1–J3 = findings_saved
[ ] Master list at top of findings.md
[ ] Success criteria met
```

---

## Next after J1–J3

- **J4** — Norway/Scandinavia (`./run-next.sh J4`)
- **Batch A** — company-deep dives for top High-fit employers from master list
- **Apply pass** — for each High fit, manual check of careers page + note requirements in findings
