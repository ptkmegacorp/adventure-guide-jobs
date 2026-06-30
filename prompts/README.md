# Job discovery prompts for LiteResearcher

How to write prompts that find **multiday trip-leading jobs** without wasting visits on generic aggregators.

## What works with LiteResearcher

LiteResearcher runs `search → visit → answer`. Good prompts:

1. **State the goal in one sentence** — what you're collecting, not why.
2. **Name anchor employers** — gives the model a similarity target (Haka Tours, Pacific Discovery, etc.).
3. **Constrain geography** — NZ, USA, Canada, Norway (our priority list).
4. **Define role types** — exact job title strings to search for.
5. **Whitelist source types** — company careers pages, niche outdoor boards.
6. **Blacklist domains** — Indeed, LinkedIn Jobs, ZipRecruiter, Glassdoor (aggregators add noise; LR visits fewer useful pages).
7. **Prefer natural compact output** — bullets, short sections, or tables are all fine as long as findings paste cleanly into `findings.md`.
8. **Ask for "currently hiring OR known seasonal recruiter"** — many adventure companies hire seasonally even when no live posting.

## Domains to avoid (always include in prompts)

```
indeed.com
linkedin.com/jobs
ziprecruiter.com
glassdoor.com
monster.com
simplyhired.com
talent.com
```

Tell the agent: **Do not search with `site:indeed.com`, do not visit Indeed URLs, do not cite Indeed listings.**

## Sources to steer toward

| Type | Examples |
|------|----------|
| Niche outdoor/travel boards | coolworks.com, backdoorjobs.com, seasonaljobs.com, workabout.co.nz |
| Industry | adventuretravel.biz (ATTA) |
| Direct | `{company}.com/careers`, `/jobs`, `/work-with-us`, `/join-our-team` |
| Operator lists | "companies like Haka Tours", "gap year program leaders" + region |

## Search query patterns (for the agent to use)

```
"trip leader" OR "driver guide" OR "field instructor" site:coolworks.com
"program leader" gap year adventure jobs New Zealand -site:indeed.com
overland tour leader hiring Canada careers -indeed
{company name} careers trip leader
workabout adventure guide jobs NZ
```

## Output notes (paste into findings.md)

Each run can return bullets, short sections, prose, or a table. Capture: company, region, role title(s), careers URL, trip length, hiring signal, and fit when available.

**Hiring signal:** `live posting` | `seasonal recruiter` | `careers page only` | `unknown`

## Running a prompt

**Agents:** background subagent only — [`../AGENTS.md`](../AGENTS.md). Never foreground + poll timers.

**Humans:**

```bash
cd /home/bot/adventure-guide-jobs
./run-next.sh J1
./run-next.sh --mark-findings J1   # after useful notes are appended to findings.md
```

Results land in `runs/`. Registry tracks state; `--mark-findings` checks off `research-prompts.md`.

## Prompt files

| ID | File | Focus |
|----|------|-------|
| J1 | `prompts/J1-active-openings.txt` | Broad discovery, all regions |
| J2 | `prompts/J2-nz-driver-guides.txt` | NZ driver-guide employers |
| J3 | `prompts/J3-us-ca-field-instructors.txt` | USA/Canada experiential education |
| J4 | `prompts/J4-norway-scandinavia.txt` | Norway / Nordics |
