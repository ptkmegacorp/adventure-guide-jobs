# Utility AI Research — Pipeline Improvements

Research note for the adventure-guide-jobs + LiteResearcher workflow.  
**Date:** 2026-06-30  
**Scope:** What utility AIs and recent literature suggest for finding, ranking, summarizing, and deduplicating multiday adventure-travel employers.

Related local docs: [`README.md`](./README.md) (job definition & taxonomy), [`AGENTS.md`](./AGENTS.md) (run loop), [`REVIEW.md`](./REVIEW.md) (salvage-first post-run).

---

## Abstract problem

This project is **employer discovery under a structured rubric**: find operators that hire multiday trip leaders (driver-guide, field instructor, program leader) in NZ / USA / Canada / Norway, extract evidence from primary sources (company sites, not aggregators), deduplicate, score fit, and maintain a living registry (`findings/candidates.json`).

In research terms this is **deep search + structured ETL + relevance ranking** — closer to lead generation and schema-bound web extraction than to resume–job matching.

Conceptual framing: [How to Use AI: What Matters](https://ptkmegacorp.github.io/how-to-use-ai-what-matters/) — assign each stage (summarize, extract, rank, merge) to a small specialized utility instead of one monolithic agent.

Survey context: [Deep Research Agents: A Systematic Examination And Roadmap](https://arxiv.org/html/2506.18096v2), [A Survey of LLM-based Deep Search Agents](https://arxiv.org/html/2508.05668v3).

---

## Current pipeline (utility mapping)

| Stage | What we do today | Utility role |
|-------|------------------|--------------|
| Scout | LiteResearcher ReAct + SearXNG | Closed-loop agent |
| Visit summarize | Qwen 3.5-4B sidecar (`:8093`) | Summarizer / condenser |
| Salvage | Re-browse visited URLs → Qwen | Summarizer (second pass) |
| Extract | `update-candidates.py` → Qwen JSON | Representation translation |
| Dedup | Hostname / normalized company name | Weak ontology |
| Rank | Fit High/Medium/Low in prompts | Implicit critic/judge |
| Guard | Aggregator blacklist in prompts + `discover-candidates.py` | Boundary / guard |
| State | `runs/registry.json`, `candidates.json`, seeds | External memory |

**Already aligned with literature:** salvage-first (LR final answer is audit-only), seed/candidate-set prompts with visit budgets, canonical JSON store. Literature supports decomposed **scout → extract → rank → merge** over single ReAct loops ([DeepDiver-DR](https://openreview.net/pdf?id=LpNR2Ajd8A), [ManuSearch](https://arxiv.org/pdf/2505.18105)).

---

## Findings — gaps and what research suggests

### 1. Anchor collapse in discovery

**Idea:** Runs converge on the same first queries and retrieve overlapping evidence (e.g. repeated anchor companies).

**Research:** [DivInit — Beyond Parallel Sampling: Diverse Query Initialization for Agentic Search](https://arxiv.org/html/2606.17209) — oversample candidate queries, select a diverse subset via Maximal Marginal Relevance (MMR) before launching parallel trajectories. [MultiSearch — Scaling Retrieval-Augmented Reasoning with Parallel Search and Explicit Merging](https://arxiv.org/html/2605.13534) — rephrase, concept expansion, and decomposition with explicit merge.

**Basic fix:** Generate many query variants from the README taxonomy; embed and MMR-pick diverse queries before search or LR runs. Complements existing `discover-candidates.py` and fixed query lists.

---

### 2. Rerank before visit

**Idea:** SearXNG returns plausible but wrong pages; each bad visit wastes the strict visit budget.

**Research:** [Rerank Before You Reason: Analyzing Reranking Tradeoffs through Effective Token Cost in Deep Search Agents](https://arxiv.org/pdf/2601.14224) — listwise reranking before the reasoning agent often beats scaling search-time reasoning on cost and accuracy.

**Models:** [BAAI/bge-reranker-v2-m3](https://huggingface.co/BAAI/bge-reranker-v2-m3) (default open cross-encoder reranker).

**Basic fix:** Rerank search snippets against the job rubric + region; visit top-k only.

---

### 3. Structured extraction

**Idea:** Freeform JSON from chat is fragile; fit labels drift run-to-run.

**Research:** [WebDART](https://doi.org/10.48550/arxiv.2510.06587) — schema-guided field extraction with dedup identifiers; [TASER](https://arxiv.org/html/2508.13404v1) — schema validation and re-extract on failure; [Nested Browser-Use Learning for Agentic Information Seeking](https://arxiv.org/pdf/2512.23647) — goal-directed JSON `{evidence, summary}` on visit.

**Models (Hugging Face):**
- [numind/NuExtract-1.5-smol](https://huggingface.co/numind/NuExtract-1.5-smol) — small schema-bound extractor
- [numind/NuExtract3](https://huggingface.co/numind/NuExtract3) — Qwen3.5-4B-based structured extraction
- [HelixCipher/job-posting-extractor-qwen](https://huggingface.co/HelixCipher/job-posting-extractor-qwen) — job-field JSON
- [Rithankoushik/job-parser-model-qwen-2.0](https://huggingface.co/Rithankoushik/job-parser-model-qwen-2.0) — anti-hallucination JD parsing

**Basic fix:** Fixed employer schema matching `candidates.json` + taxonomy enums; validate output; retry on schema failure. Visit summarization can stay on Qwen 3.5-4B.

---

### 4. Entity resolution / dedup

**Idea:** Hostname-only merge misses aliases and duplicates rows in `master.md` (same employer, different names/domains).

**Research:** [LinkTransformer: A Unified Package for Record Linkage with Transformer Language Models](https://arxiv.org/pdf/2309.00789) — semantic kNN linkage; entity-resolution pattern of embedding block → pairwise judge ([Elasticsearch Labs — Entity resolution & LLM challenges](https://www.elastic.co/search-labs/blog/entity-resolution-elasticsearch-llm-challenges)).

**Models:** [BAAI/bge-m3](https://huggingface.co/BAAI/bge-m3) for blocking; optional small LLM judge on ambiguous pairs.

**Basic fix:** Embed `(company + region + evidence)`; merge near-duplicates; escalate uncertain pairs to a judge call.

---

### 5. Explicit fit ranking

**Idea:** High/Medium/Low is prompt-defined but not consistently applied or globally ordered across runs.

**Research:** [Synapse — Evolving Job-Person Fit with Explainable Two-phase Retrieval](https://arxiv.org/pdf/2604.02539) — LLMs weak at absolute scores, strong at pairwise/listwise comparison; [ConFit v3 — Improving Resume-Job Matching with LLM-based Re-Ranking](https://arxiv.org/html/2605.09760v1) — listwise reranking in windows; [Agentic AI for Human Resources: LLM-Driven Candidate Assessment](https://arxiv.org/pdf/2603.26710) — rubric + mini-tournaments.

**Basic fix:** Encode README must-haves as a fixed rubric; listwise compare employers in small batches; store ranked order + one-line rationale.

---

### 6. Trajectory compression across runs

**Idea:** Linear ReAct re-explores; partial runs lose context; J1–J4 overlap.

**Research:** [RE-TRAC: REcursive TRAjectory Compression for Deep Search Agents](https://arxiv.org/pdf/2602.02486) — compress each trajectory to `{evidence, uncertainties, dead_ends, next_plans}`; condition the next run on that state.

**Basic fix:** After each run, sidecar compresses log to a small state file; next run prepends “already found / blocked / unexplored angles.” No LR retraining required.

---

### 7. Careers-page list extraction (scale only)

**Idea:** Bulk-verifying many seed companies’ careers pages is a different task from 8-visit scout runs.

**Research:** [WebLists: Extracting Structured Information From Complex Interactive Websites](https://arxiv.org/html/2504.12682) — careers-page list extraction benchmark; [BardeenAgent](https://www.bardeen.ai/posts/bardeenagent-introducing-the-most-reliable-research-agent) — list-mode extraction via repeatable programs.

**Basic fix:** Defer until seed lists are large; not needed for current J-prompt scout workflow.

---

### 8. Job-specific NER (optional)

**Idea:** Pull structured entities from posting text when live jobs exist.

**Model:** [AchrafSoltani/jobbert-ner-sonnet-v2](https://huggingface.co/AchrafSoltani/jobbert-ner-sonnet-v2) — SKILL, JOB_TITLE, COMPANY, LOCATION, etc.

**Basic fix:** Secondary pass on live posting pages only.

---

## Recommended priorities (Phases 1–3)

Literature and local stack suggest composing utilities **around** LiteResearcher, not replacing it.

### Phase 1 — highest ROI

| # | Idea | Primary sources |
|---|------|-----------------|
| **1** | **Rerank SearXNG results** before seeds / LR visits | [arXiv 2601.14224](https://arxiv.org/pdf/2601.14224); [bge-reranker-v2-m3](https://huggingface.co/BAAI/bge-reranker-v2-m3) |
| **2** | **DivInit-style query expansion** — diverse query pool + MMR selection | [arXiv 2606.17209](https://arxiv.org/html/2606.17209); [arXiv 2605.13534](https://arxiv.org/html/2605.13534) |
| **3** | **Schema-validated extraction** — fixed employer JSON + validation/retry | [WebDART](https://doi.org/10.48550/arxiv.2510.06587); [TASER](https://arxiv.org/html/2508.13404v1); [NuExtract](https://huggingface.co/numind/NuExtract-1.5-smol) |
| **4** | **Semantic entity merge** — embedding block + judge on ambiguous pairs | [LinkTransformer](https://arxiv.org/pdf/2309.00789); [bge-m3](https://huggingface.co/BAAI/bge-m3) |

### Phase 2

| # | Idea | Primary sources |
|---|------|-----------------|
| **5** | **Re-TRAC-lite trajectory state** between runs | [arXiv 2602.02486](https://arxiv.org/pdf/2602.02486) |
| **6** | **Listwise fit judge** on `candidates.json` | [Synapse](https://arxiv.org/pdf/2604.02539); [ConFit v3](https://arxiv.org/html/2605.09760v1); [arXiv 2603.26710](https://arxiv.org/pdf/2603.26710) |
| — | Separate **planner** (sub-questions only); execution stays LR | [GPT Researcher](https://github.com/assafelovic/gpt-researcher); [STORM](https://arxiv.org/abs/2402.14207); [ManuSearch](https://arxiv.org/pdf/2505.18105) |

### Phase 3 — if volume grows

- Fine-tuned or domain-tuned extractor on salvage logs ([NuExtract](https://huggingface.co/numind/NuExtract3), [job-posting-extractor-qwen](https://huggingface.co/HelixCipher/job-posting-extractor-qwen))
- BardeenAgent-style careers list replay for bulk seed verification ([WebLists](https://arxiv.org/html/2504.12682))
- Domain cross-encoder fine-tuned on visit-log pairs

---

## Target pipeline (conceptual)

```
EXPAND (diverse queries)
  → RETRIEVE (SearXNG)
  → RERANK (cross-encoder vs rubric)
  → SCOUT (LR visit or direct browse)
  → EXTRACT (schema-bound JSON)
  → DEDUP (embed + resolve)
  → RANK (listwise fit judge)
  → STORE (candidates.json + trajectory state)
```

Parallel inspiration: [DeepDiver-DR shared workspace](https://openreview.net/pdf?id=LpNR2Ajd8A) (planner / seeker / writer with compressed handoffs).

---

## Utility roles from “What Matters” — fit summary

| Utility | Apply? | Role here |
|---------|--------|-----------|
| Summarizer / condenser | ✅ Already | Visit + salvage + trajectory state |
| Candidate generator + reranker | ✅ Add | Query MMR + SearXNG rerank |
| Embedder | ✅ Add | Query diversity + entity dedup |
| Tagger / schema builder | ✅ Add | Taxonomy + `candidates.json` schema |
| Critic / judge | ✅ Add | Fit ranking + merge disputes |
| Guard / boundary | ✅ Partial | Extend blacklist beyond aggregators |
| Feedback control | ✅ Partial | Registry + Re-TRAC-lite state |
| Router | ◐ Optional | Discovery vs seed-verify vs salvage-only |
| Role simulator | ✗ Low value | Prompts already framed |
| UI affordance detector | ✗ N/A | Direct fetch, not browser vision |

---

## What not to do

1. **Replace LR with a monolithic deep-research API** — salvage-first design already compensates for LR weakness; add utilities around it.
2. **Rely on absolute fit scores** — prefer listwise comparison ([Synapse](https://arxiv.org/pdf/2604.02539)).
3. **Skip reranking** — often beats more agent reasoning per token ([arXiv 2601.14224](https://arxiv.org/pdf/2601.14224)).
4. **Merge by hostname alone** — adventure brands span domains and aliases.
5. **Expect resume/JD fine-tunes to transfer directly** — task is employer discovery + careers evidence, closer to [WebLists](https://arxiv.org/html/2504.12682) / lead-gen ([prospector.ai](https://github.com/SnakeyEye497/prospector.ai)) than person–job fit benchmarks.

---

## Hugging Face model shortlist

| Role | Model | Link |
|------|-------|------|
| Search rerank | BGE reranker v2 m3 | https://huggingface.co/BAAI/bge-reranker-v2-m3 |
| Dedup / MMR embeddings | BGE-M3 | https://huggingface.co/BAAI/bge-m3 |
| Structured extract (small) | NuExtract 1.5 smol | https://huggingface.co/numind/NuExtract-1.5-smol |
| Structured extract (Qwen family) | NuExtract3 | https://huggingface.co/numind/NuExtract3 |
| Job JSON extract | job-posting-extractor-qwen | https://huggingface.co/HelixCipher/job-posting-extractor-qwen |
| Job JSON extract | job-parser-model-qwen-2.0 | https://huggingface.co/Rithankoushik/job-parser-model-qwen-2.0 |
| Job posting NER | jobbert-ner-sonnet-v2 | https://huggingface.co/AchrafSoltani/jobbert-ner-sonnet-v2 |
| Visit / salvage summary | Qwen 3.5-4B (current sidecar) | local `:8093` |

---

## arXiv & papers index

| Topic | Citation |
|-------|----------|
| Trajectory compression | [RE-TRAC (2602.02486)](https://arxiv.org/pdf/2602.02486) |
| Rerank before agent reasoning | [2601.14224](https://arxiv.org/pdf/2601.14224) |
| Diverse query initialization | [DivInit (2606.17209)](https://arxiv.org/html/2606.17209) |
| Parallel search + merge | [MultiSearch (2605.13534)](https://arxiv.org/html/2605.13534) |
| Parallel sub-query RL | [ParallelSearch (2508.09303)](https://arxiv.org/abs/2508.09303) |
| Deep search survey | [2508.05668](https://arxiv.org/html/2508.05668v3) |
| Deep research roadmap | [2506.18096](https://arxiv.org/html/2506.18096v2) |
| Multi-agent deep research | [DeepDiver-DR](https://openreview.net/pdf?id=LpNR2Ajd8A) |
| Transparent search agents | [ManuSearch (2505.18105)](https://arxiv.org/pdf/2505.18105) |
| Goal-directed visit JSON | [2512.23647](https://arxiv.org/pdf/2512.23647) |
| Schema-guided extraction | [WebDART (2510.06587)](https://doi.org/10.48550/arxiv.2510.06587) |
| Schema validation loop | [TASER (2508.13404)](https://arxiv.org/html/2508.13404v1) |
| Careers list extraction | [WebLists (2504.12682)](https://arxiv.org/html/2504.12682) |
| Record linkage | [LinkTransformer (2309.00789)](https://arxiv.org/pdf/2309.00789) |
| Listwise job fit reranking | [ConFit v3 (2605.09760)](https://arxiv.org/html/2605.09760v1) |
| Pairwise fit vs absolute score | [Synapse (2604.02539)](https://arxiv.org/pdf/2604.02539) |
| Rubric + tournament ranking | [HR assessment (2603.26710)](https://arxiv.org/pdf/2603.26710) |
| Query decomposition (STORM) | [2402.14207](https://arxiv.org/abs/2402.14207) |

---

## Bottom line

The project is already a multi-utility pipeline in spirit. Research-backed additions that fit the local stack:

1. Cross-encoder rerank on search results  
2. MMR-diverse query pools for discovery  
3. Schema-validated employer extraction  
4. Embedding-based entity merge  
5. Re-TRAC-lite state between runs  
6. Listwise fit judge on the candidate registry  

Keep LiteResearcher as scout; specialize everything else.
