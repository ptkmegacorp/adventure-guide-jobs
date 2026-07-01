# Prompt changelog

Minimal edits only. Link each change to a run review.

| Date | Prompt | Run ID | Change | Reason |
|------|--------|--------|--------|--------|
| 2026-06-30 | seeds | batch-3 | Seed catalog + batch rotation; apply batch 3 slices for full J1–J4 run | shift candidate sets while preserving full catalog |
| 2026-06-30 | pipeline | local | Salvage-first default: `finalize-run.sh` auto after every run; marks saved on salvage ok | LR final answer never substantive; salvage is primary signal |
| 2026-06-30 | J2-J4 | local setup | Added `seeds/` candidate lists; changed J3/J4 from broad discovery to specific candidate-set investigation | LiteResearcher is intended for ReAct deep investigation, not first-pass lead generation |
| 2026-06-30 | LR stack | local setup | Raised LiteResearcher context 16k→32k and reduced visit content 10k→6k (49k segfaulted on this GPU) | align local setup closer to LiteResearcher long-trajectory intended use |
| 2026-06-30 | J2 | J2-20260630-173011 | Tightened to 4–6 employers, 8 visits max, anchors-only, no Workabout | context_limit_no_format ended in tool_call/no final answer |
| 2026-06-30 | J1-J4 | J1-20260630-172531 | Removed mandatory table/fixed-count output; allow natural bullets/sections/prose | user preference + context_limit_no_format |
| 2026-06-30 | J1 | J1-20260630-172531 | Skip broad J1; salvaged 2 employers; proceed J2/J3 | fail: context_limit again despite prompt trim |
| 2026-06-30 | J1 | J1-20260630-171457 | 20→10 employers; anchors-first; stop after 12 visits | review: exceed_max_turns |

## Template

```
| YYYY-MM-DD | J2 | J2-... | Reduced employer target 20→10; dropped coolworks.com | review: blocked |
```
