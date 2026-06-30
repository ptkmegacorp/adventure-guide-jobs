# Research findings

Append new entries at the top. One section per research run or company cluster.

---

## Entry template

```markdown
### [Company or topic] — YYYY-MM-DD

- **Role type:** Driver-Guide | Field Instructor | Adventure Guide | Expedition | Tour Director
- **Region:**
- **Website:**
- **Careers / jobs URL:**
- **Typical trips:** (length, audience, activities)
- **Requirements:**
- **Pay / benefits:** (if known)
- **Season / hiring cycle:**
- **Fit:** High | Medium | Low | Future
- **Notes:**
- **Source prompt:** (e.g. A1)
```

---

## Findings

### J1 runs — 2026-06-30 (no full table; skip to J2/J3)

Broad J1 failed twice (`exceed_max_turns` / `context_limit_no_format`). Salvaged from sidecar reviews:

| Company | Region | Role title(s) | Careers URL | Hiring signal | Fit | Source |
|---------|--------|---------------|-------------|---------------|-----|--------|
| Rustic Pathways | Global | Program Leader | https://rusticpathways.com/careers | live postings mentioned | High | J1 retry review |
| G Adventures | Global | Tour leader / CEO | https://www.gadventures.com/careers | careers page mentions tour leaders | High | J1 retry review |

**Blocked/inaccessible in J1:** Haka Tours careers, Flying Kiwi, Pacific Discovery `/careers` (404), Intrepid `/careers` (404).

**Decision:** Skip further J1 retries → run **J2** (NZ) and **J3** (US/CA) for regional depth.

---

### J1 attempt — 2026-06-30 run 1 (incomplete)

- **Log:** `runs/2026-06-30-171448-J1.log`
- **run_id:** J1-20260630-171457
- **Result:** LiteResearcher ran 30 tool calls (~6 min) but terminated with `exceed_max_turns` / no final table. Many target sites (CoolWorks, Workabout, several careers pages) were unreachable or empty.
- **Partial hits:** Haka Tours, G Adventures, Intrepid (tour leader roles mentioned in visits).
- **Action:** Re-run `./run-next.sh --force J1` or proceed with narrower J2/J3 prompts.

*(No employer table yet — do not mark findings_saved.)*
