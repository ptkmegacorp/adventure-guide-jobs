# Seed catalog and batch rotation

Broad employer universe lives in **`catalog/`** (never deleted — append only).

Each **batch** selects a different slice per prompt (`J1`–`J4`) for LiteResearcher scout runs.

```bash
./apply-seed-batch.sh              # apply active batch from seeds/batches.json
./apply-seed-batch.sh --batch 3    # switch to batch 3 and patch prompts
./apply-seed-batch.sh --unseen --prompt J2   # lowest-coverage J2 seeds + skip list from candidates.json
./apply-seed-batch.sh --status     # show catalog size + batch assignments + unseen preview
```

Generated per-run slices: `seeds/active/J*.txt`  
Prompt candidate sections are patched between `## Candidate set` and `## Strict visit budget`.

Legacy flat files (`J2-nz-companies.txt`, etc.) mirror the **active** batch for backwards compatibility.
