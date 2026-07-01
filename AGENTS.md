# AGENTS.md — Adventure Guide Jobs

**Read this file first.** All LiteResearcher runs use a **background subagent or background shell** — never a foreground wait with manual timers.

**Primary output:** [`findings/master.md`](./findings/master.md) + [`findings/{run_id}-salvage.md`](./findings/)  
**Run history:** [`runs/registry.json`](./runs/registry.json)

---

## Pipeline (salvage-first)

LiteResearcher **scouts URLs**; **salvage is the default findings step** (automatic via `finalize-run.sh` after every run).

```
run-next.sh
  → LiteResearcher (8092)     # visit seed/candidate URLs
  → review-run.sh             # log audit
  → extract-findings.sh       # LR final answer audit (usually empty)
  → finalize-run.sh           # DEFAULT — salvage → master → mark saved
       → salvage-run.sh       # re-browse visited URLs (8002) + Qwen (8093)
       → update-candidates.sh # findings/master.md + candidates.json
       → make-run-findings.sh
       → mark findings_saved when salvage substantive
```

---

## Execution model (required)

```
RULE: Never run ./run-next.sh in the foreground with long Await/poll timers.
      Always delegate to a background subagent OR background shell (block_until_ms=0).

PARENT AGENT on "run J2" / "run research":
  1. READ ./driver-status.sh
  2. LAUNCH background worker:

     Task(generalPurpose, run_in_background=true):
       "In /home/bot/adventure-guide-jobs:
        - Run ./run-and-save-notify.sh [--force] {prompt}
          (or ./run-next.sh {prompt} — finalize-run is built in)
        - Wait for AGENT_RUN_DONE and AGENT_RUN_FINALIZED
        - Read findings/{run_id}-salvage.md and findings/master.md
        - Return: salvage_status, employer count, top employers, driver-status"

  3. DO NOT poll with sleep/Await every N minutes
  4. DO NOT restore pig-stack unless user asks
  5. DO NOT manually salvage unless backfilling an old run
```

**Sentinels:**

```
AGENT_RUN_START     {"prompt":"J3","run_id":"...","log":"runs/..."}
AGENT_RUN_FINALIZED {"run_id":"...","salvage_status":"ok","salvage_employer_count":4,...}
AGENT_RUN_DONE      {"prompt":"J3","run_id":"...","exit_code":0,"log":"runs/..."}
```

---

## Main loop (pseudo-code)

```
ON ENTER project:
  READ ./driver-status.sh

IF user wants research AND no active run:
  DELEGATE bg subagent → ./run-and-save-notify.sh [--force] {next prompt}

ON AGENT_RUN_DONE exit 0:
  READ findings/{run_id}-salvage.md   # primary — NOT the raw log
  READ findings/master.md
  IF salvage_status == empty:
    edit prompts/ + CHANGELOG → --force retry
  ELSE:
    proceed to next prompt or consolidate

DO NOT treat review_outcome: fail as no signal when salvage_status: ok
DO NOT read runs/*.log unless salvage missing
```

---

## Registry states

| Status | Meaning |
|--------|---------|
| `pending` | Never run successfully |
| `running` | LR in progress |
| `run_done` | LR finished; finalize incomplete or partial salvage |
| `findings_saved` | Salvage (or LR answer) substantive — skip unless `--force` |

```bash
./driver-status.sh      # recommended
./run-status.sh         # registry detail
```

---

## Commands

```bash
cd /home/bot/adventure-guide-jobs

./run-next.sh J3                  # run + auto finalize (salvage)
./run-and-save-notify.sh --force J3
./finalize-run.sh --run-id RUN_ID   # backfill or re-run salvage pipeline
./save-findings.sh --run-id RUN_ID  # alias for finalize-run.sh
./driver-status.sh
./run-next.sh --force J2          # intentional re-run
```

LiteResearcher stack: LR-4B `:8092` + Qwen3.5-4B `:8093` (both GPU). Profile: `~/.config/pig-stack/profiles/literesearcher.env`.

---

## Subagent prompt template

```
Project: /home/bot/adventure-guide-jobs
Read AGENTS.md and ./driver-status.sh first.

Run: ./run-and-save-notify.sh [--force] {PROMPT_ID}

When AGENT_RUN_FINALIZED appears:
1. Read findings/{run_id}-salvage.md (primary)
2. Read findings/master.md
3. Return: salvage_status, employer count, top 5, ./driver-status.sh tail

Do not manually salvage — finalize-run is automatic.
Do not restore pig-stack.
```

---

## Prompt queue

| ID | File | Focus |
|----|------|-------|
| J1 | `prompts/J1-active-openings.txt` | Broad (usually skip) |
| J2 | `prompts/J2-nz-driver-guides.txt` | NZ driver-guides (seed list) |
| J3 | `prompts/J3-us-ca-field-instructors.txt` | US/CA candidates |
| J4 | `prompts/J4-norway-scandinavia.txt` | Norway/Nordics candidates |

Seeds: [`seeds/`](./seeds/) · Checklist: [`research-prompts.md`](./research-prompts.md)

---

## Do / Don't

| Do | Don't |
|----|-------|
| Background subagent or `block_until_ms=0` shell | Foreground run + poll timers |
| Read `findings/*-salvage.md` + `master.md` | Copy from raw LR logs |
| Trust salvage over LR review `fail` | Retry prompt because LR hit context limit |
| Use `./driver-status.sh` | Manually parse registry unless debugging |

---

## Start now (parent agent)

```
RUN ./driver-status.sh
IF prompt pending AND no active run:
  LAUNCH bg subagent → ./run-and-save-notify.sh {next prompt}
ELSE IF all findings_saved:
  review findings/master.md; --force retry weak regions if needed
```
