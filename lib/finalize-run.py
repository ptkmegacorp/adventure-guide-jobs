#!/usr/bin/env python3
"""Default post-run pipeline: salvage → update-candidates → per-run findings → mark saved."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "runs" / "registry.json"


def load_registry() -> dict[str, Any]:
    with REGISTRY.open(encoding="utf-8") as f:
        return json.load(f)


def save_registry(data: dict[str, Any]) -> None:
    with REGISTRY.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def find_run(data: dict[str, Any], run_id: str) -> dict[str, Any]:
    for run in data.get("runs", []):
        if run.get("run_id") == run_id:
            return run
    raise SystemExit(f"run_id not found: {run_id}")


def count_employers(summary: str) -> int:
    if not summary.strip():
        return 0
    n = len(re.findall(r"^#{1,4}\s+\d+\.\s+", summary, re.M))
    if n:
        return n
    n = len(re.findall(r"^\*\s+\*\*Company:\*\*", summary, re.M))
    if n:
        return n
    # Bullets with company names and hiring signals
    n = len(re.findall(r"^\*\s+\*\*[^*]+?\*\*", summary, re.M))
    return max(n, 1 if len(summary.strip()) >= 200 else 0)


def salvage_quality(summary: str) -> tuple[str, int]:
    summary = (summary or "").strip()
    count = count_employers(summary)
    if count >= 1 and len(summary) >= 200:
        return "ok", count
    if summary:
        return "partial", count
    return "empty", 0


def run_cmd(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True)


def extract_summary_text(salvage_path: Path) -> str:
    text = salvage_path.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"## Qwen salvage summary\s*\n+(.*?)(?:\n## |\Z)", text, re.S)
    return m.group(1).strip() if m else ""


def mark_run_saved(data: dict[str, Any], run: dict[str, Any]) -> None:
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    run["findings_saved"] = True
    pid = run.get("prompt_id")
    if not pid:
        return
    ps = data.setdefault("prompts", {}).setdefault(pid, {})
    ps["status"] = "findings_saved"
    ps["findings_saved_at"] = now
    ps["last_log"] = run.get("log")
    if run.get("findings_path"):
        ps["last_findings"] = run.get("findings_path")
        ps["last_findings_status"] = run.get("findings_status")
    if run.get("salvage_path"):
        ps["last_salvage"] = run.get("salvage_path")
        ps["last_salvage_status"] = run.get("salvage_status")

    prompts_md = ROOT / "research-prompts.md"
    if prompts_md.exists():
        text = prompts_md.read_text(encoding="utf-8")
        unchecked = f"- [ ] **{pid}."
        checked = f"- [x] **{pid}."
        if unchecked in text:
            prompts_md.write_text(text.replace(unchecked, checked, 1), encoding="utf-8")


def finalize(run_id: str, *, skip_salvage: bool = False, force_salvage: bool = False) -> dict[str, Any]:
    data = load_registry()
    run = find_run(data, run_id)
    if run.get("status") not in ("completed", "failed"):
        raise SystemExit(f"run {run_id} is not finished (status={run.get('status')})")

    result: dict[str, Any] = {
        "run_id": run_id,
        "prompt_id": run.get("prompt_id"),
        "salvage_path": run.get("salvage_path"),
        "salvage_status": run.get("salvage_status"),
        "salvage_employer_count": run.get("salvage_employer_count"),
        "findings_path": run.get("findings_path"),
        "findings_saved": run.get("findings_saved", False),
        "master_updated": False,
    }

    need_salvage = (
        not skip_salvage
        and (force_salvage or not run.get("salvage_path") or run.get("salvage_status") in (None, "empty"))
    )
    if need_salvage:
        proc = run_cmd([sys.executable, str(ROOT / "lib" / "salvage-run.py"), "--run-id", run_id])
        if proc.returncode != 0:
            result["salvage_error"] = (proc.stderr or proc.stdout or "salvage failed").strip()
        data = load_registry()
        run = find_run(data, run_id)

    salvage_rel = run.get("salvage_path")
    if salvage_rel:
        summary = extract_summary_text(ROOT / salvage_rel)
        status, count = salvage_quality(summary)
        run["salvage_status"] = status
        run["salvage_employer_count"] = count
        ps = data.setdefault("prompts", {}).setdefault(run.get("prompt_id", "?"), {})
        ps["last_salvage"] = salvage_rel
        ps["last_salvage_status"] = status
        ps["salvage_employer_count"] = count
        save_registry(data)
        result["salvage_path"] = salvage_rel
        result["salvage_status"] = status
        result["salvage_employer_count"] = count

    if run.get("salvage_status") in ("ok", "partial") and salvage_rel:
        proc = run_cmd(
            [
                sys.executable,
                str(ROOT / "lib" / "update-candidates.py"),
                "--from-file",
                salvage_rel,
                "--source-run",
                run_id,
            ]
        )
        if proc.returncode == 0:
            result["master_updated"] = True
            result["update_candidates"] = (proc.stdout or "").strip()
        else:
            result["update_candidates_error"] = (proc.stderr or proc.stdout or "update failed").strip()

    proc = run_cmd([sys.executable, str(ROOT / "lib" / "make-run-findings.py"), "--run-id", run_id])
    if proc.returncode == 0:
        result["findings_path"] = (proc.stdout or "").strip()
    data = load_registry()
    run = find_run(data, run_id)

    substantive = (
        run.get("salvage_status") == "ok"
        or int(run.get("salvage_employer_count") or 0) >= 1
        or int(run.get("answer_chars") or 0) >= 100
    )
    if substantive and not run.get("findings_saved"):
        mark_run_saved(data, run)
        save_registry(data)
        result["findings_saved"] = True
    else:
        result["findings_saved"] = bool(run.get("findings_saved"))
        if not substantive:
            result["findings_saved_reason"] = "no substantive salvage or LR answer"

    return result


def main() -> None:
    ap = argparse.ArgumentParser(description="Finalize a completed run (salvage-first pipeline)")
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--skip-salvage", action="store_true")
    ap.add_argument("--force-salvage", action="store_true")
    ap.add_argument("--json", action="store_true", help="Print JSON result")
    args = ap.parse_args()
    out = finalize(args.run_id, skip_salvage=args.skip_salvage, force_salvage=args.force_salvage)
    if args.json:
        print(json.dumps(out))
    else:
        print(
            f"finalized {out['run_id']}: salvage={out.get('salvage_status')} "
            f"employers={out.get('salvage_employer_count')} "
            f"saved={'yes' if out.get('findings_saved') else 'no'} "
            f"master={'yes' if out.get('master_updated') else 'no'}"
        )
        if out.get("findings_path"):
            print(f"findings: {out['findings_path']}")
        if out.get("salvage_path"):
            print(f"salvage: {out['salvage_path']}")


if __name__ == "__main__":
    main()
