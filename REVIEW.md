# Review loop — adjust prompts from run results

After every literesearcher run, use deterministic extraction plus the **sidecar** (Qwen3.5-4B `:8093`) for compression. Don't feed raw logs to the main agent.

---

## Flow (pseudo-code)

```
ON AGENT_RUN_DONE:
  RUN ./review-run.sh --prompt {id}
  READ reviews/{run_id}.md          # ~1 page, not the full log

  SWITCH review.next_action:
    mark_findings:
      RUN ./save-findings.sh --run-id {run_id}
    edit_prompt_retry:
      READ ## Prompt feedback from review
      EDIT prompts/{id}-*.txt (minimal change)
      LOG change in prompts/CHANGELOG.md
      RUN ./run-next.sh --force {id}   # bg subagent
    skip_to_next_prompt:
      LOG note in findings.md + CHANGELOG
      RUN next prompt (J2, J3, ...)
    consolidate:
      merge master list (AGENTS.md)
```

---

## Commands

```bash
./review-run.sh --prompt J1       # review latest J1 run
./review-run.sh --run-id J1-...   # specific run
./review-run.sh --no-sidecar      # extractive only (8093 down)
```

Output: `reviews/{run_id}.md` + registry fields `review_outcome`, `review_next_action`. Successful runs are also extracted to `runs/extracted/{run_id}.md`.

---

## What to change in prompts (keep focused)

Only adjust these levers — don't rewrite whole prompts each time:

| Lever | When |
|-------|------|
| **Scope** | `exceed_max_turns` → fewer regions or "find 10 not 20" |
| **Sources** | URL blocked in review → remove from whitelist, add working alternative |
| **Output** | No useful final answer → ask for shorter natural notes, fewer visit rounds |
| **Depth** | Broad J1 fails → skip to regional J2/J3 instead of retrying J1 |

Log every edit in [`prompts/CHANGELOG.md`](./CHANGELOG.md) with run_id + one-line reason.

---

## Sidecar role

| Model | Port | Job |
|-------|------|-----|
| LiteResearcher-4B | 8092 | Research (search/visit loop) |
| Qwen3.5-4B | 8093 | Page extraction **+ run log review** |

Review sends a **compressed excerpt** (~visit URLs, termination, prediction snippet) — not the full log — to `:8093` for structured markdown review.

---

## Outcomes

| Outcome | Meaning |
|---------|---------|
| `success` | Useful final employer notes present → mark_findings |
| `partial` | Some URLs worked, but no useful final notes → salvage + edit prompt or skip |
| `fail` | Max turns / no data → edit prompt or skip to next prompt |

---

## Files

```
reviews/{run_id}.md       ← sidecar-compressed review
runs/extracted/{run_id}.md ← deterministic final-answer extraction
prompts/CHANGELOG.md      ← prompt edits paper trail
runs/registry.json        ← review/extraction/save state
```
