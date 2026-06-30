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

### J2 run — 2026-06-30 (partial; no table)

- **Log:** `runs/2026-06-30-173000-J2.log`
- **run_id:** J2-20260630-173011
- **Result:** 23 tool calls, terminated `context_limit_no_format` — visited many NZ operators but no final markdown table.
- **Review:** `reviews/J2-20260630-173011.md` (extractive; treat as **partial**, not success)

| Company | Region | Role / signal | URL visited | Fit | Source |
|---------|--------|---------------|-------------|-----|--------|
| Haka Tours | NZ | Guide / driver-guide content | https://hakatours.com/blog/what-it-takes-to-be-a-haka-tours-guide | High | J2 log |
| Flying Kiwi | NZ | Careers + about explored | https://www.flyingkiwi.com/careers | High | J2 log |
| Stray Travel | NZ | Careers + about explored | https://www.straytravel.com/careers | High | J2 log |
| Active Adventures | NZ | Driver-guide hiring mentioned | https://activeadventures.com/get-your-new-zealand-guide | High | J2 log |
| Kiwi Experience | NZ | Bus driver-guides page | https://www.kiwiexperience.com/about-kiwi-experience/driver-guides | High | J2 log |
| Adventure Junkies | NZ | Driver guides confirmed in visit | https://www.adventurejunkies.com/ | Med | J2 log |
| Wild Kiwi | NZ | Site visited; roles not fully extracted | https://www.wildkiwi.com/ | Med | J2 log |

**Blocked/unreachable:** workabout.co.nz (http + https), several generic searches returned no results.

**Next:** Tighten J2 prompt (e.g. 8 employers, stop after 10 visits, prose bullets OK) and `--force J2`, or proceed **J3** (US/CA).

---

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


