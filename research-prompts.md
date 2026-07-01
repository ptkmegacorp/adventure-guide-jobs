# Literesearcher prompt queue

Rotate through these; mark **Done** with date when findings are copied to `findings.md`.

Run: `./run-next.sh` or `./run-batch.sh` from this directory.

**Agents:** background subagent only — see [`AGENTS.md`](./AGENTS.md). Never foreground the script.

Status key: `[ ]` pending · `[x]` done (synced by `--mark-findings`)

---

## Batch J — Job discovery (start here)

Full prompt text in `prompts/J*.txt`. All prompts **exclude Indeed and generic aggregators**.

- [x] **J1.** Broad active openings — **skipped after 2 failed runs**; partial salvage in findings → `prompts/J1-active-openings.txt`

- [x] **J2.** NZ driver-guides and trip leaders (Workabout, operator careers) → `prompts/J2-nz-driver-guides.txt`

- [x] **J3.** USA/Canada field instructors & program leaders → `prompts/J3-us-ca-field-instructors.txt`

- [x] **J4.** Norway / Scandinavia multiday trip leaders → `prompts/J4-norway-scandinavia.txt`

---

## Batch A — Companies like our anchors (NZ / USA / Canada / Norway)

> **Superseded for NZ:** use `./apply-seed-batch.sh --unseen --prompt J2` + `./run-next.sh --force J2` instead of A1. J2 has no anchor homepages; `--unseen` picks fresh catalog seeds and auto-skips well-researched employers from `findings/candidates.json`.

- [x] **A1.** List adventure tour companies in **New Zealand** similar to Haka Tours — **superseded by J2 `--unseen`** (A1 revisited known anchors)

- [ ] **A2.** List experiential education and gap year organizations in the **USA and Canada** similar to Pacific Discovery that hire field instructors or program leaders (2–12 week programs).

- [ ] **A3.** List adventure tour and overland companies in **Norway and Scandinavia** that hire multiday trip leaders, guides, or driver-guides.

- [ ] **A4.** Which small-group adventure travel companies (6–16 guests) hire trip leaders in **New Zealand, USA, Canada, and Norway**?

---

## Batch B — Job titles & boards

- [ ] **B1.** Where are "field instructor" or "program leader" jobs for gap year travel posted online? List specific job boards and example active listings if any.

- [ ] **B2.** Best job boards and websites for adventure tour guide and driver-guide jobs in **New Zealand, USA, Canada, and Norway** (2025–2026).

- [ ] **B3.** What job titles do G Adventures and Intrepid Travel use for their on-trip leaders in **North America and Europe**, and what are typical requirements and pay?

- [ ] **B4.** CoolWorks, Workabout, and Backdoor Jobs: which categories list multiday trip leader roles in **USA, Canada, and NZ**?

---

## Batch C — Requirements & pathways

- [ ] **C1.** What certifications are commonly required for Pacific Discovery–style field instructors (first aid, WFR, lifeguard, driving license class)?

- [ ] **C2.** How do people typically get hired as a Haka Tours or NZ adventure driver-guide with no prior guiding experience? Training programs or pathways?

- [ ] **C3.** Compare field instructor vs tour driver-guide roles: duties, season length, pay, and lifestyle.

- [ ] **C4.** Student travel companies hiring trip leaders in the United States for summer 2026 (Rustic Pathways, ARCC, Broadreach, similar).

---

## Batch D — Niche expansions

- [ ] **D1.** Marine conservation and reef programs that hire field staff or trip leaders for multiday programs (Hawaii, Caribbean, similar to Pacific Discovery marine programs).

- [ ] **D2.** Rafting and multiday river guide employers that also need trip logistics leaders (not just day raft guide).

- [ ] **D3.** Bicycle tour companies hiring multiday trip leaders in Europe or Americas.

- [ ] **D4.** Women's adventure travel companies and retreat leaders hiring for multiday international trips.

---

## Done log

| ID | Date | One-line result |
|----|------|-----------------|
| — | — | — |
