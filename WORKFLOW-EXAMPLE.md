# Workflow example — deterministic research loop

This project uses scripts for state and file writes. The main model should read concise status and run the recommended command, not inspect raw logs unless something is broken.

## Normal loop

```bash
cd /home/bot/adventure-guide-jobs
./driver-status.sh
```

If no run is active and a prompt is pending, start the next research run in the background per `AGENTS.md`:

```bash
./run-next.sh J3
```

`run-next.sh` will:

1. register the run in `runs/registry.json`
2. run LiteResearcher
3. write the raw log in `runs/`
4. run `review-run.sh` for a short review in `reviews/`
5. run `extract-findings.sh` to save a deterministic final-answer extract in `runs/extracted/`

## After a run finishes

Check status:

```bash
./driver-status.sh
```

If the recommended command is extraction:

```bash
./extract-findings.sh --run-id RUN_ID
```

If the extracted answer is substantive, save it:

```bash
./save-findings.sh --run-id RUN_ID
```

`save-findings.sh` writes `findings/RUN_ID.md`. It marks the prompt `findings_saved` only when the run has a substantive final answer; partial/no-final-answer runs still get a per-run findings file.

## If extraction refuses to save

This means the run did not produce a user-facing final answer. Common case: LiteResearcher hit `context_limit_no_format` and ended with a `<tool_call>` instead of findings.

Do **not** mark findings saved. The per-run file can still capture review notes and visit evidence. Then:

1. read `findings/RUN_ID.md` and `reviews/RUN_ID.md`
2. salvage any useful notes manually only if they are clearly evidenced
3. tighten the prompt or proceed to the next prompt

Example:

```bash
./review-run.sh --run-id RUN_ID
# then either edit prompt + retry, or run the next prompt
```

## Registry states

- `pending`: not completed yet
- `running`: active LiteResearcher/GPU job
- `run_done`: run completed; findings not saved
- `findings_extracted`: extracted markdown exists in `runs/extracted/`
- `findings_saved`: extracted/curated findings have been appended to `findings.md`

## Division of responsibility

- Scripts own state transitions and writes.
- Sidecar summarizes/reviews logs.
- Main model reads `driver-status.sh` and handles exceptional cases.
- Raw logs are last resort; prefer `reviews/` and `runs/extracted/`.
