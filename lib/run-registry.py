#!/usr/bin/env python3
"""Run registry for adventure-guide-jobs literesearcher loop."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "runs" / "registry.json"
PROMPTS_MD = ROOT / "research-prompts.md"


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def load_registry() -> dict[str, Any]:
    if not REGISTRY.exists():
        return {"version": 1, "runs": [], "prompts": {}}
    with REGISTRY.open(encoding="utf-8") as f:
        return json.load(f)


def save_registry(data: dict[str, Any]) -> None:
    REGISTRY.parent.mkdir(parents=True, exist_ok=True)
    with REGISTRY.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def prompt_state(data: dict[str, Any], prompt_id: str) -> dict[str, Any]:
    return data.setdefault("prompts", {}).setdefault(
        prompt_id,
        {
            "status": "pending",  # pending | run_done | findings_saved | done
            "run_count": 0,
            "last_run_at": None,
            "last_log": None,
            "findings_saved_at": None,
        },
    )


def is_prompt_complete(data: dict[str, Any], prompt_id: str) -> bool:
    st = prompt_state(data, prompt_id).get("status", "pending")
    return st in ("findings_saved", "done")


def latest_run_for_prompt(data: dict[str, Any], prompt_id: str) -> dict[str, Any] | None:
    matches = [r for r in data.get("runs", []) if r.get("prompt_id") == prompt_id]
    if not matches:
        return None
    return sorted(matches, key=lambda r: r.get("started_at", ""))[-1]


def start_run(prompt_id: str, log_path: str, prompt_file: str) -> str:
    data = load_registry()
    run_id = f"{prompt_id}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    entry = {
        "run_id": run_id,
        "prompt_id": prompt_id,
        "prompt_file": prompt_file,
        "log": log_path,
        "started_at": _now(),
        "finished_at": None,
        "exit_code": None,
        "status": "running",
        "findings_saved": False,
    }
    data.setdefault("runs", []).append(entry)
    ps = prompt_state(data, prompt_id)
    ps["run_count"] = int(ps.get("run_count") or 0) + 1
    ps["status"] = "running"
    ps["last_run_at"] = entry["started_at"]
    ps["last_log"] = log_path
    save_registry(data)
    return run_id


def finish_run(run_id: str, exit_code: int) -> None:
    data = load_registry()
    for run in data.get("runs", []):
        if run.get("run_id") == run_id:
            run["finished_at"] = _now()
            run["exit_code"] = exit_code
            run["status"] = "completed" if exit_code == 0 else "failed"
            ps = prompt_state(data, run["prompt_id"])
            ps["last_run_at"] = run["finished_at"]
            ps["last_log"] = run.get("log")
            if exit_code == 0:
                ps["status"] = "run_done"
            else:
                ps["status"] = "pending"
            save_registry(data)
            return
    raise SystemExit(f"run_id not found: {run_id}")


def mark_findings_saved(prompt_id: str, log_path: str | None = None) -> None:
    data = load_registry()
    ps = prompt_state(data, prompt_id)
    ps["status"] = "findings_saved"
    ps["findings_saved_at"] = _now()
    if log_path:
        ps["last_log"] = log_path
    for run in reversed(data.get("runs", [])):
        if run.get("prompt_id") == prompt_id and run.get("status") == "completed":
            if log_path is None or run.get("log") == log_path:
                run["findings_saved"] = True
                break
    save_registry(data)
    _sync_prompts_md_check(prompt_id)


def _sync_prompts_md_check(prompt_id: str) -> None:
    if not PROMPTS_MD.exists():
        return
    text = PROMPTS_MD.read_text(encoding="utf-8")
    unchecked = f"- [ ] **{prompt_id}."
    checked = f"- [x] **{prompt_id}."
    if unchecked in text:
        PROMPTS_MD.write_text(text.replace(unchecked, checked, 1), encoding="utf-8")


def any_running(data: dict[str, Any] | None = None) -> bool:
    if data is None:
        data = load_registry()
    return any(r.get("status") == "running" for r in data.get("runs", []))


def next_pending_prompt(data: dict[str, Any] | None = None) -> str | None:
    if data is None:
        data = load_registry()
    order = ["J1", "J2", "J3", "J4"]
    for pid in order:
        if prompt_state(data, pid).get("status") == "running":
            continue
        if not is_prompt_complete(data, pid):
            return pid
    return None


def print_status() -> None:
    data = load_registry()
    runs = data.get("runs", [])
    print(f"Registry: {REGISTRY.relative_to(ROOT)}")
    print(f"Total runs: {len(runs)}")
    print()
    print("Prompt status:")
    for pid in ["J1", "J2", "J3", "J4"]:
        ps = prompt_state(data, pid)
        last = latest_run_for_prompt(data, pid)
        log = ps.get("last_log") or (last or {}).get("log") or "—"
        rev = ps.get("last_review_outcome") or "—"
        print(
            f"  {pid}: {ps.get('status', 'pending'):14} "
            f"runs={ps.get('run_count', 0)}  review={rev}  last_log={log}"
        )
    nxt = next_pending_prompt(data)
    print()
    if nxt:
        print(f"Next suggested: {nxt}")
    else:
        print("All J1–J4 findings saved — run consolidate (see AGENTS.md)")
    if runs:
        print()
        print("Recent runs (newest first):")
        for run in sorted(runs, key=lambda r: r.get("started_at", ""), reverse=True)[:8]:
            print(
                f"  {run.get('run_id')}  {run.get('status')}  "
                f"exit={run.get('exit_code')}  review={run.get('review_outcome', '—')}  "
                f"log={run.get('log')}"
            )


def main() -> None:
    if len(sys.argv) < 2:
        print_status()
        return
    cmd = sys.argv[1]
    if cmd == "status":
        print_status()
    elif cmd == "next":
        nxt = next_pending_prompt()
        print(nxt or "")
    elif cmd == "start":
        run_id = start_run(sys.argv[2], sys.argv[3], sys.argv[4])
        print(run_id)
    elif cmd == "finish":
        finish_run(sys.argv[2], int(sys.argv[3]))
    elif cmd == "complete":
        prompt_id = sys.argv[2]
        mark_findings_saved(prompt_id, sys.argv[3] if len(sys.argv) > 3 else None)
        print(f"marked findings saved: {prompt_id}")
    elif cmd == "is-complete":
        print("yes" if is_prompt_complete(load_registry(), sys.argv[2]) else "no")
    elif cmd == "any-running":
        print("yes" if any_running(load_registry()) else "no")
    else:
        raise SystemExit(f"unknown command: {cmd}")


if __name__ == "__main__":
    main()
