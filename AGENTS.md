# AGENTS.md — Adventure Guide Jobs

**Read this file first.** All LiteResearcher runs use a **background subagent or background shell** — never a foreground wait with manual timers.

**Output:** [`findings.md`](./findings.md)  
**Run history:** [`runs/registry.json`](./runs/registry.json)

---

## Execution model (required)

```
RULE: Never run ./run-next.sh or ./run-batch.sh in the foreground with long Await/poll timers.
      Always delegate to a background subagent OR background shell (block_until_ms=0).

PARENT AGENT on "run J1" / "run research":
  1. READ runs/registry.json  (or ./run-status.sh)
  2. LAUNCH background worker (pick one):

     Option A — Task subagent (preferred for full handoff):
       Task(generalPurpose, run_in_background=true):
         "In /home/bot/adventure-guide-jobs:
          - Run ./run-next.sh {prompt}  (or ./run-batch.sh for J1 J2 J3)
          - Wait for AGENT_RUN_DONE in output (exit_code 0)
          - Read log path from AGENT_RUN_DONE JSON
          - Append useful final-answer notes → findings.md
          - Run ./run-next.sh --mark-findings {prompt}
          - Return summary: employer count, log path, registry status"
       RETURN to user: 'J1 started in background subagent — will process when done'
       ON subagent completion notification → relay results to user

     Option B — background shell (same machine, no subagent):
       Shell(block_until_ms=0): cd /home/bot/adventure-guide-jobs && ./run-next.sh J1
       ON shell completion notification:
         grep AGENT_RUN_DONE in terminal output
         READ log from JSON → findings.md → --mark-findings

  3. DO NOT poll with sleep/Await every N minutes
  4. DO NOT restore pig-stack unless user asks
```

**Sentinels** (scripts print these for the worker to parse):

```
AGENT_RUN_START {"prompt":"J1","run_id":"...","log":"runs/..."}
AGENT_RUN_DONE  {"prompt":"J1","run_id":"...","exit_code":0,"log":"runs/..."}
AGENT_BATCH_DONE {"prompts":"J1 J2 J3"}   # run-batch.sh only
```

---

## Main loop (pseudo-code)

```
ON ENTER project:
  READ runs/registry.json
  IF user wants research AND no bg job already running:
    DELEGATE to background subagent (see above)
  ELSE IF bg job completed since last turn:
    PROCESS AGENT_RUN_DONE → findings.md → --mark-findings
  ELSE:
    REPORT ./run-status.sh to user

FOR EACH AGENT_RUN_DONE with exit_code 0:
  READ AGENT_RUN_REVIEW → auto-runs ./review-run.sh (sidecar :8093 or extractive fallback)
  READ reviews/{run_id}.md     # short — NOT the full log

  SWITCH review.next_action:
    mark_findings  → append useful final-answer notes → findings.md → --mark-findings
    edit_prompt_retry → edit prompts/ + CHANGELOG → bg subagent --force {id}
    skip_to_next_prompt → note in findings.md → bg subagent next prompt
    consolidate → master list

  DO NOT read runs/*.log directly unless review file missing

consolidate_master_list:
  IF J1,J2,J3 all findings_saved AND no "## Master list" in findings.md:
    MERGE + DEDUPE → prepend Master list
```

---

## Registry states

| Status | Meaning |
|--------|---------|
| `pending` | Never run successfully |
| `running` | In progress (interrupted run → re-delegate) |
| `run_done` | LR finished; worker must append useful findings + `--mark-findings` |
| `findings_saved` | Done; skip unless `--force` |

```bash
./run-status.sh
```

---

## Commands (for the subagent / bg shell to run)

```bash
cd /home/bot/adventure-guide-jobs

./run-next.sh J1              # one prompt (~15–25 min)
./run-batch.sh                # J1 → J2 → J3 (~1–1.5 hr)
./run-next.sh --mark-findings J1   # after findings.md updated
./run-status.sh
./run-next.sh --force J2      # intentional re-run only
./run-next.sh --dry-run J1    # preview prompt, no LR
```

LiteResearcher stack: LR-4B `:8092` + Qwen3.5-4B summary `:8093` (both GPU). Profile: `~/.config/pig-stack/profiles/literesearcher.env`.

---

## Subagent prompt template (copy-paste)

```
Project: /home/bot/adventure-guide-jobs
Read AGENTS.md and runs/registry.json first.

Run: ./run-next.sh {PROMPT_ID}
(or ./run-batch.sh for J1 J2 J3)

When AGENT_RUN_DONE appears with exit_code 0:
1. Read the log file from the JSON "log" field
2. Extract the useful employer notes from the final answer (table, bullets, or prose)
3. Append to findings.md with run_id and log path
4. Run ./run-next.sh --mark-findings {PROMPT_ID}
5. Run ./run-status.sh
6. Return: row count, top 5 employers, next suggested prompt

If exit_code != 0: report error, suggest retry with ./run-next.sh --force {PROMPT_ID}
Do not restore pig-stack.
```

---

## Prompt queue

| ID | File | Focus |
|----|------|-------|
| J1 | `prompts/J1-active-openings.txt` | Broad, all regions |
| J2 | `prompts/J2-nz-driver-guides.txt` | NZ driver-guides |
| J3 | `prompts/J3-us-ca-field-instructors.txt` | USA/Canada field instructors |
| J4 | `prompts/J4-norway-scandinavia.txt` | Norway (after J1–J3) |

Checklist mirror: [`research-prompts.md`](./research-prompts.md)

---

## Do / Don't

| Do | Don't |
|----|-------|
| Background subagent or `block_until_ms=0` shell | Foreground run + 10m Await loops |
| Wait for completion notification | Poll `./run-status.sh` on a timer |
| Parse `AGENT_RUN_DONE` then post-process | Ignore registry / skip `--mark-findings` |
| Check registry before launching | Re-run `findings_saved` prompts without `--force` |

---

## Start now (parent agent)

```
RUN ./run-status.sh
IF prompt pending AND no active bg research job:
  LAUNCH Task subagent (run_in_background=true) with template above for next prompt
  TELL user job is running in background
ELSE IF last bg job completed:
  PROCESS findings from AGENT_RUN_DONE
ELSE IF J1–J3 all findings_saved:
  consolidate_master_list OR launch J4
```
