# Adventure Guide Jobs — Research Project

A living list of **multiday trip-leading roles** (driver-guide, field instructor, trip leader) in NZ, USA, Canada, and Norway.

**Agents:** read [`AGENTS.md`](./AGENTS.md) first — **always run research via a background subagent** (never foreground + manual timers).  
**Humans:** `./run-batch.sh` or `./run-next.sh J1` in a terminal; results land in `runs/`.

---

## Quick start

```
# Parent agent — delegate, do not block:
Task(subagent, run_in_background=true) → run ./run-next.sh J1 per AGENTS.md
# OR: Shell(block_until_ms=0) ./run-next.sh J1
# Wait for completion notification → AGENT_RUN_DONE → findings.md

# Human — direct:
cd /home/bot/adventure-guide-jobs
./run-batch.sh              # J1 → J2 → J3
./run-status.sh             # registry view
./driver-status.sh          # concise driver view + recommended next command
./run-and-save-notify.sh J3 # run, save per-run findings, notify active Pi agent
```

After each `AGENT_RUN_DONE`: `extract-findings.sh` writes `runs/extracted/…`; then run `./save-findings.sh --run-id RUN_ID` to write `findings/RUN_ID.md` and mark saved only when there is a substantive final answer.

Registry: [`runs/registry.json`](./runs/registry.json) · **[`AGENTS.md`](./AGENTS.md)** (full loop)

| Doc | Purpose |
|-----|---------|
| [`AGENTS.md`](./AGENTS.md) | **Main loop** + `runs/registry.json` state machine |
| [`run-status.sh`](./run-status.sh) | What's run, what's next |
| [`PLAN-J1-J3.md`](./PLAN-J1-J3.md) | Checklist + success criteria |
| [`REVIEW.md`](./REVIEW.md) | Post-run review loop + prompt adjustments |
| [`review-run.sh`](./review-run.sh) | Sidecar-compressed run review |
| [`extract-findings.sh`](./extract-findings.sh) | Deterministically extracts final answer to `runs/extracted/` |
| [`save-findings.sh`](./save-findings.sh) | Writes per-run `findings/RUN_ID.md`; marks registry saved only for substantive answers |
| [`driver-status.sh`](./driver-status.sh) | Concise deterministic status/recommended next step |
| [`run-and-save-notify.sh`](./run-and-save-notify.sh) | Self-contained run → findings → Pi agent notification wrapper |
| [`reviews/`](./reviews/) | Short review per run (read these, not raw logs) |
| [`prompts/CHANGELOG.md`](./prompts/CHANGELOG.md) | Prompt edit paper trail |
| [Job definition](#what-im-looking-for-working-definition) | What counts as a fit |

LiteResearcher runs via [`literesearcher-app`](../projects/literesearcher-app) — stops Pig `:8091` while active; no need to switch pig-stack profiles afterward unless you want voice/Pig back.

---

## What I'm looking for (working definition)

**Core role:** Lead a small group on a **multiday trip** (typically 3 days to 3 months), where I'm responsible for **group experience, safety, logistics, and often driving or moving the group between places** — not a desk job, not a single-day city walking tour.

**Must-haves**

| Criterion | Notes |
|-----------|-------|
| Multiday | Overnight trips; not day-only gigs |
| Lead / guide / instruct | I'm the person the group looks to, not back-office ops |
| Travel & outdoors | Nature, adventure, or immersive cultural travel — not conference/event staffing |
| Small groups | Roughly 6–20 people; not mass tourism |

**Strong preferences**

| Criterion | Notes |
|-----------|-------|
| Drive + guide combo | Overland van/bus, 4WD, or similar — like many NZ / overland operators |
| Young-adult / student / gap-year audience | Pacific Discovery–style experiential programs (any audience OK) |
| International or domestic adventure | OK with seasonal contracts and passport-friendly employers |
| Mix of facilitation + activity | Hiking, surf, conservation, cultural immersion — not pure shuttle driving |

**Geographic focus**

| Priority | Regions |
|----------|---------|
| Primary | New Zealand, USA, Canada, Norway |
| Also OK | Global — include if role fits, but weight search toward the four above |

**Timing:** Any season — no restriction on start date or hiring cycle.

**Probably not a fit**

- Single-day city tour guide (unless it's a stepping stone)
- Cruise ship entertainment / hospitality without leading trips
- Pure sales / travel agent (no field time)
- Resort activity staff with no multiday leadership
- Heavy certification barriers I don't have yet (e.g. IFMGA mountain guide) — note as "future path" not immediate target

---

## Role types (taxonomy)

Use these labels when logging companies in `findings.md`.

### 1. Driver-Guide / Overland Leader

Drive the vehicle **and** guide the trip. Common in New Zealand, Australia, Africa, South America.

**Typical duties:** Drive van or bus; route planning; commentary; meal/camp logistics; first aid; sometimes light hiking activity leadership.

**Reference companies**

| Company | Region | Why it fits |
|---------|--------|-------------|
| [Haka Tours](https://www.hakatours.com) | New Zealand | Classic NZ adventure tours; driver-guides on multiday loops |
| [Flying Kiwi](https://www.flyingkiwi.com) | New Zealand | Overland-style; flexible hop-on trips |
| [Stray Travel](https://www.straytravel.com) | NZ / Asia / Latin America | Hop-on hop-off adventure network |
| [Intrepid Travel](https://www.intrepidtravel.com) | Global | Small-group adventure; many trips use dedicated leaders |
| [G Adventures](https://www.gadventures.com) | Global | Similar tier; CEO (Chief Experience Officer) roles |
| [Overland Escape](https://www.overlandescape.com) | Various | Overland truck/van expeditions |
| [Dragoman](https://www.dragoman.com) | Global overland | Long multiday overland truck trips |

### 2. Field Instructor / Program Leader (experiential education)

Lead **gap year, study abroad, or summer programs** for teens and young adults. Heavy on facilitation, curriculum, risk management, and group dynamics.

**Typical duties:** Co-lead with another instructor; daily program delivery; service-learning or conservation modules; student welfare; budgets and logistics with HQ support.

**Reference companies**

| Company | Region | Why it fits |
|---------|--------|-------------|
| [Pacific Discovery](https://www.pacificdiscovery.org) | Global (NZ, Pacific, Americas, Asia) | Gap semesters & summer programs; "instructor" model |
| [Where There Be Dragons](https://www.wheretherebedragons.com) | Global | Gap year & summer immersive programs |
| [ARCC Programs](https://www.adventurescrosscountry.com) | Americas | Teen adventure & service trips |
| [Rustic Pathways](https://www.rusticpathways.com) | Global | Student travel & service |
| [Broadreach](https://www.gobroadreach.com) | Global | Marine, scuba, outdoor programs for students |
| [NOLS](https://www.nols.edu) | USA / international | Wilderness education; field instructor track |
| [Outward Bound](https://www.outwardbound.org) | Various | Expedition-based youth/adult programs |

### 3. Adventure Tour Guide (activity-forward, may not drive)

Multiday hiking, rafting, kayaking, or lodge-to-lodge trips. May subcontract to tour operators.

**Examples:** REI Adventures trip leaders, regional rafting outfitters, trekking companies (e.g. Macs Adventure trip hosts, Exodus trip leaders).

### 4. Expedition / Trip Leader (higher commitment)

Longer or harder trips: polar, high-altitude trekking support roles, multi-week expeditions. Often needs more certs or a progression path.

**Examples:** Antarctic support staff with guiding duties, Kilimanjaro lead guides (often local + international assistant), long-distance trekking companies.

### 5. Tour Director / Trip Manager (soft adventure)

More logistics and group management; less rugged. Still multiday. Useful if adventure brands also hire TDs for easier departures.

**Examples:** Some Contiki / Topdeck / Trafalgar-style roles — lower priority unless marketed as "adventure" departures.

---

## Reference anchors (what "like this" means)

### Haka Tours–like

- **Product:** Scheduled multiday NZ adventure tours (e.g. 3–24 days)
- **Vibe:** Social backpacker / young traveler; active (hike, kayak, Māori culture)
- **Role name signals:** *Tour guide, driver-guide, adventure guide*
- **Seasonality:** Often peak NZ summer (Oct–Apr)

### Pacific Discovery–like

- **Product:** Gap semesters (10 weeks), mini-semesters, summer programs (2–6 weeks)
- **Vibe:** Experiential education — service, conservation, cultural immersion, outdoor skills
- **Role name signals:** *Field instructor, program leader, trip leader, guru instructor*
- **Audience:** Gap year & college-age; parents trust safety/risk systems

---

## Search keywords (for literesearcher & job boards)

**Job titles**

```
driver guide
overland leader
tour leader adventure
field instructor gap year
program leader experiential education
trip leader small group travel
CEO chief experience officer  (G Adventures)
adventure tour guide multiday
expedition leader
```

**Company-type queries**

```
companies like Haka Tours hiring guide
companies like Pacific Discovery field instructor
overland tour companies hiring driver guide
gap year program leaders hiring 2026
small group adventure travel employers
New Zealand tour operator guide jobs
experiential education travel instructor jobs
```

**Job boards & aggregators to hit (by region)**

- **NZ:** [Workabout](https://www.workabout.co.nz)
- **USA / Canada:** [CoolWorks](https://www.coolworks.com), [Backdoor Jobs](https://www.backdoorjobs.com), [SeasonalJobs.com](https://seasonaljobs.com)
- **Norway / Nordics:** company career pages (Hvitserk, Active Adventures Norway, Norwegian tour operators)
- **Global:** [Adventure Travel Trade Association careers](https://www.adventuretravel.biz)

---

## Research workflow

**Agents:** background subagent only — see [`AGENTS.md`](./AGENTS.md).

**Humans:**

```bash
./run-batch.sh              # J1 → J2 → J3
./run-next.sh J1
./run-status.sh
```

**What to extract from each run**

- Company name, URL, region
- Role type (from taxonomy above)
- Typical season / contract length
- Hiring page or "work with us" URL
- Requirements (license, first aid, age, experience)
- Pay range if published
- Fit score: **High / Medium / Low / Future** + one sentence why

---

## Open questions (fill in as we learn)

- [x] Preferred regions → **NZ, USA, Canada, Norway** (global OK, weighted to these)
- [x] Audience → **any**
- [x] Season → **any**
- [ ] Willing to get/commercial driver's license or specific certs (WFR, lifeguard, etc.)?
- [ ] Minimum pay / room & board expectations?
- [ ] Age restrictions on some student-travel instructor roles?

---

## Files in this folder

| File | Purpose |
|------|---------|
| `AGENTS.md` | **Agent workflow** — start here for automation |
| `README.md` | Job definition, taxonomy, quick start |
| `PLAN-J1-J3.md` | J1→J2→J3 execution plan |
| `run-batch.sh` | Run J1 J2 J3 (or custom list) sequentially |
| `run-next.sh` | Run one literesearcher prompt → `runs/` |
| `prompts/` | Full prompt text (J1–J4) + writing guide |
| `research-prompts.md` | Queue checklist |
| `findings/` | Per-run findings, legacy archive, and curated `master.md` |
| `run-status.sh` | Show run history + next pending prompt |
| `runs/registry.json` | **Loop state** — all past runs, prompt status |
| `runs/` | Raw logs (referenced by registry) |
