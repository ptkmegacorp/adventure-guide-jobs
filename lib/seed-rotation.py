#!/usr/bin/env python3
"""Seed catalog + batch rotation for adventure-guide-jobs prompts."""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
SEEDS = ROOT / "seeds"
CATALOG = SEEDS / "catalog.json"
BATCHES = SEEDS / "batches.json"
ACTIVE_DIR = SEEDS / "active"
PROMPTS = ROOT / "prompts"
MARKER_START = "## Candidate set"
MARKER_END = "## Strict visit budget"


def now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_catalog() -> dict[str, dict[str, Any]]:
    return load_json(CATALOG)


def load_batches() -> dict[str, Any]:
    return load_json(BATCHES)


def catalog_by_id(catalog: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for pid, rows in catalog.items():
        for row in rows:
            out[row["id"]] = {**row, "prompt_id": pid}
    return out


def batch_lines(batch: int, prompt_id: str, catalog: dict[str, dict[str, Any]], by_id: dict[str, dict[str, Any]]) -> list[str]:
    cfg = load_batches()
    ids = cfg.get("batches", {}).get(str(batch), {}).get(prompt_id, [])
    lines = []
    for sid in ids:
        row = by_id.get(sid)
        if not row:
            raise SystemExit(f"unknown seed id {sid!r} for {prompt_id} batch {batch}")
        lines.append(f"- {row['company']} — {row['url']}")
    return lines


def write_active_slice(batch: int, prompt_id: str, lines: list[str]) -> Path:
    ACTIVE_DIR.mkdir(parents=True, exist_ok=True)
    out = ACTIVE_DIR / f"{prompt_id}.txt"
    body = [
        f"# Active seed slice — {prompt_id} batch {batch}",
        f"# generated: {now()}",
        "",
        *lines,
        "",
    ]
    out.write_text("\n".join(body), encoding="utf-8")
    return out


def write_legacy_mirror(prompt_id: str, lines: list[str], batch: int) -> None:
    names = {
        "J1": "J1-global-employers.txt",
        "J2": "J2-nz-companies.txt",
        "J3": "J3-us-ca-field-instructors.txt",
        "J4": "J4-nordics-companies.txt",
    }
    path = SEEDS / names[prompt_id]
    body = [f"# Company | URL | active batch {batch} slice", ""]
    for line in lines:
        m = re.match(r"-\s+(.+?)\s+—\s+(https?://\S+)", line)
        if m:
            body.append(f"{m.group(1)} | {m.group(2)} | catalog slice batch {batch}")
    path.write_text("\n".join(body) + "\n", encoding="utf-8")


def patch_prompt(prompt_id: str, lines: list[str], batch: int) -> Path:
    matches = list(PROMPTS.glob(f"{prompt_id}-*.txt"))
    if not matches:
        raise SystemExit(f"no prompt file for {prompt_id}")
    path = matches[0]
    text = path.read_text(encoding="utf-8")
    start = text.find(MARKER_START)
    end = text.find(MARKER_END)
    if start < 0 or end < 0 or end <= start:
        raise SystemExit(f"prompt markers not found in {path.name}")
    header = f"{MARKER_START} — batch {batch} (inspect these first)"
    block = header + "\n" + "\n".join(lines) + "\n\n"
    new_text = text[:start] + block + text[end:]
    path.write_text(new_text, encoding="utf-8")
    return path


def apply_batch(batch: int | None = None, prompt_ids: list[str] | None = None) -> dict[str, Any]:
    cfg = load_batches()
    batch = batch if batch is not None else int(cfg.get("active_batch", 1))
    catalog = load_catalog()
    by_id = catalog_by_id(catalog)
    pids = prompt_ids or ["J1", "J2", "J3", "J4"]
    applied: dict[str, Any] = {"batch": batch, "prompts": {}}
    for pid in pids:
        lines = batch_lines(batch, pid, catalog, by_id)
        active = write_active_slice(batch, pid, lines)
        prompt = patch_prompt(pid, lines, batch)
        write_legacy_mirror(pid, lines, batch)
        applied["prompts"][pid] = {
            "count": len(lines),
            "active": str(active.relative_to(ROOT)),
            "prompt": str(prompt.relative_to(ROOT)),
            "seed_ids": cfg["batches"][str(batch)][pid],
        }
    cfg["active_batch"] = batch
    for h in cfg.get("history", []):
        if int(h.get("batch", 0)) == batch:
            h["applied_at"] = now()
    save_json(BATCHES, cfg)
    applied["active_batch"] = batch
    return applied


def status() -> None:
    cfg = load_batches()
    catalog = load_catalog()
    by_id = catalog_by_id(catalog)
    print(f"active_batch: {cfg.get('active_batch')}")
    print(f"catalog entries: {len(by_id)}")
    for pid in ["J1", "J2", "J3", "J4"]:
        n = len(catalog.get(pid, []))
        active = cfg.get("batches", {}).get(str(cfg.get("active_batch")), {}).get(pid, [])
        print(f"  {pid}: catalog={n} active_slice={len(active)}")
    print("\nBatch history:")
    for h in cfg.get("history", []):
        print(f"  batch {h.get('batch')}: applied_at={h.get('applied_at')} — {h.get('note')}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Apply seed catalog batch slices to prompts")
    ap.add_argument("--batch", type=int, help="Batch number to apply (default: active_batch)")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--prompt", action="append", choices=["J1", "J2", "J3", "J4"])
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    if args.status:
        status()
        return
    out = apply_batch(args.batch, args.prompt)
    if args.json:
        print(json.dumps(out))
    else:
        print(f"applied batch {out['batch']}")
        for pid, info in out["prompts"].items():
            print(f"  {pid}: {info['count']} seeds -> {info['prompt']}")


if __name__ == "__main__":
    main()
