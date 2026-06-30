#!/usr/bin/env python3
"""Deterministically extract the final LiteResearcher answer for a run."""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "runs" / "registry.json"
EXTRACTED_DIR = ROOT / "runs" / "extracted"


def load_registry() -> dict[str, Any]:
    with REGISTRY.open(encoding="utf-8") as f:
        return json.load(f)


def save_registry(data: dict[str, Any]) -> None:
    with REGISTRY.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def find_run(data: dict[str, Any], run_id: str | None, prompt_id: str | None) -> dict[str, Any]:
    runs = data.get("runs", [])
    if run_id:
        for r in runs:
            if r.get("run_id") == run_id:
                return r
        raise SystemExit(f"run_id not found: {run_id}")
    if prompt_id:
        matches = [r for r in runs if r.get("prompt_id") == prompt_id and r.get("status") == "completed"]
    else:
        matches = [r for r in runs if r.get("status") == "completed" and not r.get("findings_saved")]
    if not matches:
        raise SystemExit("no matching completed unsaved run")
    return sorted(matches, key=lambda r: r.get("started_at", ""))[-1]


def clean_answer(answer: str) -> str:
    answer = answer.strip()
    # A context-limit run may end with model internals or another tool call instead
    # of a user-facing answer. Treat that as no final answer.
    stripped = re.sub(r"<think>.*?</think>", "", answer, flags=re.S).strip()
    if not stripped or stripped.startswith("<tool_call>") or "</tool_call>" in stripped:
        return ""
    return answer


def extract_final_answer(text: str) -> str:
    # Prefer final smoke-test prediction block.
    matches = list(re.finditer(r"(?:^|\n)prediction:\s*(.*?)(?=\ntermination:|\ntool_calls:|\ntools used:|\nPASS\b|\Z)", text, re.S))
    if matches:
        return clean_answer(matches[-1].group(1))
    matches = list(re.finditer(r"(?:^|\n)\[answer\]\s*(.*?)(?=\n\[[a-z_]+\]|\Z)", text, re.S))
    if matches:
        return clean_answer(matches[-1].group(1))
    return ""


def run_stats(text: str) -> dict[str, Any]:
    def one(pattern: str) -> str | None:
        m = re.search(pattern, text)
        return m.group(1) if m else None
    visits = re.findall(r"\[visit\]\s*(\{.+?\})\s*\n", text, re.S)
    urls: list[str] = []
    for raw in visits:
        try:
            payload = json.loads(raw)
            u = payload.get("url") or []
            if isinstance(u, str):
                u = [u]
            urls.extend(str(x) for x in u)
        except json.JSONDecodeError:
            pass
    return {
        "termination": one(r"termination:\s*(\S+)"),
        "tool_calls": int(one(r"tool_calls:\s*(\d+)") or 0),
        "visited_urls": urls[:50],
    }


def attach(data: dict[str, Any], run_id: str, rel_path: str, answer_chars: int) -> None:
    for r in data.get("runs", []):
        if r.get("run_id") == run_id:
            r["extracted_path"] = rel_path
            r["extracted_at"] = now()
            r["answer_chars"] = answer_chars
            r["extraction_status"] = "ok" if answer_chars >= 100 else "no_final_answer"
            pid = r.get("prompt_id")
            if pid:
                ps = data.setdefault("prompts", {}).setdefault(pid, {})
                ps["last_extracted"] = rel_path
                ps["last_extraction_status"] = r["extraction_status"]
                if ps.get("status") == "run_done" and r["extraction_status"] == "ok":
                    ps["status"] = "findings_extracted"
            return


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id")
    ap.add_argument("--prompt")
    ap.add_argument("--print", action="store_true", help="print extracted markdown path")
    args = ap.parse_args()

    data = load_registry()
    run = find_run(data, args.run_id, args.prompt)
    log_rel = run.get("log")
    if not log_rel:
        raise SystemExit("run has no log")
    log_path = ROOT / log_rel
    text = log_path.read_text(encoding="utf-8", errors="replace")
    answer = extract_final_answer(text)
    stats = run_stats(text)

    EXTRACTED_DIR.mkdir(parents=True, exist_ok=True)
    out = EXTRACTED_DIR / f"{run['run_id']}.md"
    content = f"""# Extracted findings — {run['run_id']}

- **prompt:** {run.get('prompt_id')}
- **log:** `{log_rel}`
- **extracted_at:** {now()}
- **termination:** `{stats.get('termination')}`
- **tool_calls:** {stats.get('tool_calls')}
- **answer_chars:** {len(answer)}

## Final answer

{answer or '_No final answer extracted._'}

## Visited URLs

"""
    content += "\n".join(f"- {u}" for u in stats.get("visited_urls", [])[:30]) or "_none extracted_"
    content += "\n"
    out.write_text(content, encoding="utf-8")

    rel = str(out.relative_to(ROOT))
    attach(data, run["run_id"], rel, len(answer))
    save_registry(data)
    if args.print:
        print(rel)
    else:
        print(f"extracted {run['run_id']} -> {rel} ({len(answer)} chars)")


if __name__ == "__main__":
    main()
