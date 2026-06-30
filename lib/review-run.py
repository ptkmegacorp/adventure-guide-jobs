#!/usr/bin/env python3
"""Review a literesearcher run log — extractive parse + Qwen sidecar summary."""

from __future__ import annotations

import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "runs" / "registry.json"
REVIEWS_DIR = ROOT / "reviews"
PROMPTS_DIR = ROOT / "prompts"
CHANGELOG = PROMPTS_DIR / "CHANGELOG.md"

# Sidecar (literesearcher visit summarizer) — same as browser_server
SUMMARY_API = "http://127.0.0.1:8093/v1/chat/completions"
SUMMARY_MODEL = "qwen3.5-4b-summary-local"


def load_registry() -> dict[str, Any]:
    with REGISTRY.open(encoding="utf-8") as f:
        return json.load(f)


def save_registry(data: dict[str, Any]) -> None:
    with REGISTRY.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def find_run(*, run_id: str | None, prompt_id: str | None, log_path: str | None) -> dict[str, Any]:
    data = load_registry()
    runs = data.get("runs", [])
    if run_id:
        for r in runs:
            if r.get("run_id") == run_id:
                return r
        raise SystemExit(f"run_id not found: {run_id}")
    if log_path:
        for r in runs:
            if r.get("log") == log_path or r.get("log", "").endswith(log_path):
                return r
    if prompt_id:
        matches = [r for r in runs if r.get("prompt_id") == prompt_id]
        if matches:
            return sorted(matches, key=lambda r: r.get("started_at", ""))[-1]
    raise SystemExit("specify --run-id, --prompt, or --log")


def has_useful_final_answer(text: str) -> bool:
    """True if the run produced a substantive final answer, table or not."""
    for marker in ("prediction:", "[answer]"):
        idx = text.rfind(marker)
        if idx < 0:
            continue
        tail = text[idx : idx + 5000]
        answer = re.sub(r"termination:.*", "", tail, flags=re.S).strip()
        if len(answer) > 300 and re.search(r"careers?|jobs?|hiring|guide|leader|instructor|employer", answer, re.I):
            return True
    return False


def parse_log(text: str) -> dict[str, Any]:
    termination = None
    prediction = None
    tool_calls = None
    tools_used: list[str] = []

    m = re.search(r"termination:\s*(\S+)", text)
    if m:
        termination = m.group(1)
    m = re.search(r"prediction:\s*(.+?)(?:\ntermination:|\n---|\Z)", text, re.S)
    if m:
        prediction = m.group(1).strip()[:2000]

    m = re.search(r"tool_calls:\s*(\d+)", text)
    if m:
        tool_calls = int(m.group(1))
    m = re.search(r"tools used:\s*(\[.+?\])", text)
    if m:
        try:
            tools_used = json.loads(m.group(1).replace("'", '"'))
        except json.JSONDecodeError:
            tools_used = []

    visits: list[dict[str, str]] = []
    for vm in re.finditer(r"\[visit\]\s*(\{.+?\})\s*\n\[visit_result\]", text, re.S):
        try:
            payload = json.loads(vm.group(1))
            urls = payload.get("url") or []
            if isinstance(urls, str):
                urls = [urls]
            for url in urls[:4]:
                visits.append({"url": url, "goal": str(payload.get("goal", ""))[:120]})
        except json.JSONDecodeError:
            continue

    visit_outcomes: list[dict[str, str]] = []
    for vm in re.finditer(
        r"\[visit_result\]\s*The useful information in (\S+) for user goal (.+?) as follows:\s*\n\nEvidence in page:\s*\n(.{0,200})",
        text,
        re.S,
    ):
        visit_outcomes.append(
            {
                "url": vm.group(1),
                "goal": vm.group(2).strip()[:80],
                "evidence_preview": vm.group(3).replace("\n", " ").strip(),
            }
        )

    searches: list[str] = []
    for sm in re.finditer(r'\[search\]\s*(\{.+?\})', text):
        try:
            q = json.loads(sm.group(1)).get("query", [])
            if isinstance(q, list):
                searches.extend(q[:3])
            else:
                searches.append(str(q))
        except json.JSONDecodeError:
            pass

    blocked = [v for v in visit_outcomes if "could not be accessed" in v["evidence_preview"].lower()]
    empty = [v for v in visit_outcomes if "no results" in v["evidence_preview"].lower()]

    has_final_answer = has_useful_final_answer(text)

    return {
        "termination": termination,
        "prediction_preview": prediction,
        "tool_calls": tool_calls,
        "tools_used": tools_used,
        "visit_count": len(visits),
        "searches_sample": searches[:12],
        "visit_outcomes": visit_outcomes[:20],
        "blocked_visits": [b["url"] for b in blocked],
        "has_useful_final_answer": has_final_answer,
        "has_employer_table": has_final_answer,
    }


def compress_for_sidecar(parsed: dict[str, Any], log_path: str, prompt_id: str) -> str:
    lines = [
        f"prompt_id: {prompt_id}",
        f"log: {log_path}",
        f"termination: {parsed.get('termination')}",
        f"tool_calls: {parsed.get('tool_calls')}",
        f"has_useful_final_answer: {parsed.get('has_useful_final_answer')}",
        f"prediction_preview: {parsed.get('prediction_preview', '')[:800]}",
        "",
        "searches_sample:",
        *[f"  - {q}" for q in parsed.get("searches_sample", [])],
        "",
        "visit_outcomes (url | evidence snippet):",
    ]
    for v in parsed.get("visit_outcomes", [])[:15]:
        lines.append(f"  - {v['url']}: {v['evidence_preview'][:120]}")
    lines.append("")
    lines.append(f"blocked_urls: {parsed.get('blocked_urls', parsed.get('blocked_visits', []))}")
    return "\n".join(lines)[:12000]


REVIEW_SYSTEM = """You review LiteResearcher job-discovery run logs for adventure-guide trip leader roles.
Output ONLY markdown with these sections (keep each section short):

## Outcome
One of: success | partial | fail — one sentence why.

## Employers found
Bullet list: Company | region if known | hiring signal | URL (or "none" if zero)

## Sources
- Worked: URLs that returned useful employer/careers info
- Blocked/empty: URLs that failed or had no listings

## Prompt feedback
Max 3 bullets: what to change in the research prompt next time (scope, sources, output format). Natural prose or bullets are fine; do not require tables.

## Next action
Exactly one: mark_findings | edit_prompt_retry | skip_to_next_prompt | consolidate

Be factual. Do not invent employers not evidenced in the log excerpt."""


def call_sidecar(excerpt: str) -> str | None:
    body = json.dumps(
        {
            "model": SUMMARY_MODEL,
            "messages": [
                {"role": "system", "content": REVIEW_SYSTEM},
                {"role": "user", "content": f"Review this run excerpt:\n\n{excerpt}"},
            ],
            "temperature": 0.2,
            "max_tokens": 1200,
        }
    ).encode()
    req = urllib.request.Request(
        SUMMARY_API,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            data = json.load(resp)
        return (data["choices"][0]["message"]["content"] or "").strip()
    except (urllib.error.URLError, TimeoutError, KeyError, json.JSONDecodeError) as e:
        return None


def extractive_review(parsed: dict[str, Any]) -> str:
    term = parsed.get("termination") or "unknown"
    if parsed.get("has_useful_final_answer") or parsed.get("has_employer_table"):
        outcome = "success"
        action = "mark_findings"
    elif term in ("exceed_max_turns", "context_limit_no_format", "timeout"):
        outcome = "partial" if parsed.get("visit_outcomes") else "fail"
        action = "edit_prompt_retry"
    elif parsed.get("visit_outcomes"):
        outcome = "partial"
        action = "edit_prompt_retry"
    else:
        outcome = "fail"
        action = "skip_to_next_prompt"

    blocked = parsed.get("blocked_visits") or []
    useful = [
        v["url"]
        for v in parsed.get("visit_outcomes", [])
        if "could not be accessed" not in v.get("evidence_preview", "").lower()
    ]

    return f"""## Outcome
{outcome} — termination={term}, tool_calls={parsed.get('tool_calls')}, final_answer={'yes' if parsed.get('has_useful_final_answer') else 'no'}

## Employers found
(none extracted — see prediction_preview in run stats)

## Sources
- Worked: {', '.join(useful[:8]) or 'none identified'}
- Blocked/empty: {', '.join(blocked[:8]) or 'none listed'}

## Prompt feedback
- Reduce scope if exceed_max_turns (fewer regions or employers per run)
- Drop or replace blocked source domains in prompt whitelist
- Ask for fewer employers with deeper visits (e.g. 10 not 20)

## Next action
{action}
"""


def parse_outcome(review_md: str) -> str:
    m = re.search(r"## Outcome\s*\n\s*(success|partial|fail)", review_md, re.I)
    return m.group(1).lower() if m else "unknown"


def parse_next_action(review_md: str) -> str:
    m = re.search(
        r"## Next action\s*\n\s*(mark_findings|edit_prompt_retry|skip_to_next_prompt|consolidate)",
        review_md,
        re.I,
    )
    return m.group(1).lower() if m else "unknown"


def write_review(
    run: dict[str, Any],
    parsed: dict[str, Any],
    review_body: str,
    *,
    sidecar_used: bool,
) -> Path:
    REVIEWS_DIR.mkdir(parents=True, exist_ok=True)
    run_id = run["run_id"]
    out = REVIEWS_DIR / f"{run_id}.md"
    outcome = parse_outcome(review_body)
    action = parse_next_action(review_body)

    content = f"""# Run review — {run_id}

- **prompt:** {run.get('prompt_id')}
- **log:** `{run.get('log')}`
- **reviewed_at:** auto
- **sidecar:** {'qwen3.5-4b @ :8093' if sidecar_used else 'extractive fallback'}
- **outcome:** {outcome}
- **next_action:** {action}

## Stats
- termination: `{parsed.get('termination')}`
- tool_calls: {parsed.get('tool_calls')}
- visits: {parsed.get('visit_count')}
- has_useful_final_answer: {parsed.get('has_useful_final_answer')}

{review_body}

---
See [REVIEW.md](../REVIEW.md) for the review loop.
"""
    out.write_text(content, encoding="utf-8")
    return out


def attach_review_to_registry(run_id: str, review_path: str, outcome: str, next_action: str) -> None:
    data = load_registry()
    rel = str(Path(review_path).relative_to(ROOT))
    for run in data.get("runs", []):
        if run.get("run_id") == run_id:
            run["review_path"] = rel
            run["review_outcome"] = outcome
            run["review_next_action"] = next_action
            pid = run.get("prompt_id")
            if pid:
                ps = data.setdefault("prompts", {}).setdefault(pid, {})
                ps["last_review"] = rel
                ps["last_review_outcome"] = outcome
                ps["last_review_action"] = next_action
            break
    save_registry(data)


def review_run(run: dict[str, Any], *, use_sidecar: bool = True) -> Path:
    log_rel = run.get("log", "")
    log_path = ROOT / log_rel
    if not log_path.is_file():
        raise SystemExit(f"log not found: {log_path}")

    text = log_path.read_text(encoding="utf-8", errors="replace")
    parsed = parse_log(text)
    excerpt = compress_for_sidecar(parsed, log_rel, run.get("prompt_id", "?"))

    review_body = None
    sidecar_used = False
    if use_sidecar:
        review_body = call_sidecar(excerpt)
        sidecar_used = review_body is not None

    if not review_body:
        review_body = extractive_review(parsed)

    out = write_review(run, parsed, review_body, sidecar_used=sidecar_used)
    attach_review_to_registry(
        run["run_id"],
        str(out),
        parse_outcome(review_body),
        parse_next_action(review_body),
    )
    return out


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser(description="Review a literesearcher run log")
    ap.add_argument("--prompt", help="Latest run for prompt id (J1, J2, ...)")
    ap.add_argument("--run-id", help="Specific run_id from registry")
    ap.add_argument("--log", help="Log path relative to project root")
    ap.add_argument("--no-sidecar", action="store_true", help="Extractive only")
    args = ap.parse_args()

    if not any([args.prompt, args.run_id, args.log]):
        ap.error("one of --prompt, --run-id, --log required")

    run = find_run(run_id=args.run_id, prompt_id=args.prompt, log_path=args.log)
    out = review_run(run, use_sidecar=not args.no_sidecar)
    print(out.relative_to(ROOT))
    print(f"outcome={parse_outcome(out.read_text())} next={parse_next_action(out.read_text())}")


if __name__ == "__main__":
    main()
