#!/usr/bin/env python3
"""Seed catalog + batch rotation for adventure-guide-jobs prompts."""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
SEEDS = ROOT / "seeds"
CATALOG = SEEDS / "catalog.json"
BATCHES = SEEDS / "batches.json"
CANDIDATES = ROOT / "findings" / "candidates.json"
ACTIVE_DIR = SEEDS / "active"
PROMPTS = ROOT / "prompts"
MARKER_START = "## Candidate set"
MARKER_END = "## Strict visit budget"
SKIP_START = "## Already researched — DO NOT VISIT"
STRONG_SIGNALS = {"live", "careers", "work-with-us", "seasonal"}


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


def load_candidates() -> list[dict[str, Any]]:
    if not CANDIDATES.exists():
        return []
    return load_json(CANDIDATES).get("candidates", [])


def host(url: str) -> str:
    try:
        return urlparse(url or "").netloc.lower().removeprefix("www.")
    except Exception:
        return ""


def candidate_index(candidates: list[dict[str, Any]]) -> tuple[dict[str, dict], dict[str, dict]]:
    by_host: dict[str, dict] = {}
    by_company: dict[str, dict] = {}
    for c in candidates:
        h = host(c.get("primary_url") or c.get("careers_url"))
        if h:
            by_host[h] = c
        by_company[(c.get("company") or "").lower()] = c
    return by_host, by_company


def seed_coverage(row: dict[str, Any], by_host: dict, by_company: dict) -> dict[str, Any]:
    h = host(row.get("url", ""))
    c = by_host.get(h) or by_company.get(row.get("company", "").lower())
    if not c:
        return {"seen": False, "score": 0, "runs": 0, "signal": None}
    sig = (c.get("signal_strength") or "unknown").lower()
    runs = len(c.get("source_runs") or [])
    score = runs * 10
    if sig in STRONG_SIGNALS:
        score += 50
    elif sig == "watchlist":
        score += 15
    elif sig == "inaccessible":
        score += 20
    return {"seen": True, "score": score, "runs": runs, "signal": sig}


def pick_unseen_seed_ids(prompt_id: str, limit: int = 10) -> list[str]:
    catalog = load_catalog()
    rows = catalog.get(prompt_id, [])
    by_host, by_company = candidate_index(load_candidates())
    scored = [(row, seed_coverage(row, by_host, by_company)) for row in rows]
    scored.sort(key=lambda item: (item[1]["score"], item[0]["company"]))
    return [row["id"] for row, _ in scored[:limit]]


def skip_researched_lines(prompt_id: str) -> list[str]:
    catalog = load_catalog()
    by_host, by_company = candidate_index(load_candidates())
    lines: list[str] = []
    for row in catalog.get(prompt_id, []):
        cov = seed_coverage(row, by_host, by_company)
        if not cov["seen"]:
            continue
        if cov["runs"] >= 2 or cov["signal"] in STRONG_SIGNALS:
            sig = cov["signal"] or "seen"
            lines.append(
                f"- {row['company']} — {row['url']} ({sig}, {cov['runs']} prior run(s))"
            )
    return lines


def catalog_by_id(catalog: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for pid, rows in catalog.items():
        for row in rows:
            out[row["id"]] = {**row, "prompt_id": pid}
    return out


def ids_to_lines(ids: list[str], by_id: dict[str, dict[str, Any]]) -> list[str]:
    lines = []
    for sid in ids:
        row = by_id.get(sid)
        if not row:
            raise SystemExit(f"unknown seed id {sid!r}")
        lines.append(f"- {row['company']} — {row['url']}")
    return lines


def batch_lines(batch: int, prompt_id: str, catalog: dict[str, dict[str, Any]], by_id: dict[str, dict[str, Any]]) -> list[str]:
    cfg = load_batches()
    ids = cfg.get("batches", {}).get(str(batch), {}).get(prompt_id, [])
    return ids_to_lines(ids, by_id)


def write_active_slice(batch: int, prompt_id: str, lines: list[str], *, label: str = "") -> Path:
    ACTIVE_DIR.mkdir(parents=True, exist_ok=True)
    out = ACTIVE_DIR / f"{prompt_id}.txt"
    tag = label or f"batch {batch}"
    body = [
        f"# Active seed slice — {prompt_id} {tag}",
        f"# generated: {now()}",
        "",
        *lines,
        "",
    ]
    out.write_text("\n".join(body), encoding="utf-8")
    return out


def write_legacy_mirror(prompt_id: str, lines: list[str], batch: int, *, label: str = "") -> None:
    names = {
        "J1": "J1-global-employers.txt",
        "J2": "J2-nz-companies.txt",
        "J3": "J3-us-ca-field-instructors.txt",
        "J4": "J4-nordics-companies.txt",
    }
    path = SEEDS / names[prompt_id]
    tag = label or f"batch {batch}"
    body = [f"# Company | URL | active {tag} slice", ""]
    for line in lines:
        m = re.match(r"-\s+(.+?)\s+—\s+(https?://\S+)", line)
        if m:
            body.append(f"{m.group(1)} | {m.group(2)} | catalog slice {tag}")
    path.write_text("\n".join(body) + "\n", encoding="utf-8")


def patch_prompt(
    prompt_id: str,
    lines: list[str],
    batch: int,
    *,
    skip_lines: list[str] | None = None,
    slice_label: str = "",
) -> Path:
    matches = list(PROMPTS.glob(f"{prompt_id}-*.txt"))
    if not matches:
        raise SystemExit(f"no prompt file for {prompt_id}")
    path = matches[0]
    text = path.read_text(encoding="utf-8")
    start = text.find(MARKER_START)
    end = text.find(MARKER_END)
    if start < 0 or end < 0 or end <= start:
        raise SystemExit(f"prompt markers not found in {path.name}")

    label = slice_label or f"batch {batch}"
    header = f"{MARKER_START} — {label} (inspect these first)"
    block = header + "\n" + "\n".join(lines) + "\n\n"
    new_text = text[:start] + block + text[end:]

    if skip_lines is not None and SKIP_START in new_text:
        skip_end = new_text.find(MARKER_START)
        skip_block = SKIP_START + "\n" + "\n".join(skip_lines or ["- (none)"]) + "\n\n"
        skip_start = new_text.find(SKIP_START)
        new_text = new_text[:skip_start] + skip_block + new_text[skip_end:]

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


def apply_unseen(prompt_ids: list[str] | None = None, limit: int = 10) -> dict[str, Any]:
    cfg = load_batches()
    catalog = load_catalog()
    by_id = catalog_by_id(catalog)
    pids = prompt_ids or ["J2"]
    batch_num = max(int(k) for k in cfg.get("batches", {}).keys()) + 1
    batch_key = str(batch_num)
    cfg.setdefault("batches", {})[batch_key] = {}
    applied: dict[str, Any] = {"batch": batch_num, "mode": "unseen", "prompts": {}}
    for pid in pids:
        seed_ids = pick_unseen_seed_ids(pid, limit)
        lines = ids_to_lines(seed_ids, by_id)
        skip = skip_researched_lines(pid)
        cfg["batches"][batch_key][pid] = seed_ids
        active = write_active_slice(batch_num, pid, lines, label="unseen slice")
        prompt = patch_prompt(
            pid,
            lines,
            batch_num,
            skip_lines=skip,
            slice_label=f"unseen slice (batch {batch_num})",
        )
        write_legacy_mirror(pid, lines, batch_num, label="unseen")
        applied["prompts"][pid] = {
            "count": len(lines),
            "skip_count": len(skip),
            "active": str(active.relative_to(ROOT)),
            "prompt": str(prompt.relative_to(ROOT)),
            "seed_ids": seed_ids,
        }
    cfg["active_batch"] = batch_num
    cfg.setdefault("history", []).append(
        {
            "batch": batch_num,
            "applied_at": now(),
            "note": f"unseen slice — lowest-coverage seeds from candidates.json ({', '.join(pids)})",
        }
    )
    save_json(BATCHES, cfg)
    applied["active_batch"] = batch_num
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
    print("\nUnseen J2 preview (next --unseen slice):")
    for sid in pick_unseen_seed_ids("J2", 10):
        row = by_id[sid]
        print(f"  {row['company']} — {row['url']}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Apply seed catalog batch slices to prompts")
    ap.add_argument("--batch", type=int, help="Batch number to apply (default: active_batch)")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--unseen", action="store_true", help="Pick lowest-coverage seeds from candidates.json")
    ap.add_argument("--limit", type=int, default=10, help="Max seeds for --unseen (default: 10)")
    ap.add_argument("--prompt", action="append", choices=["J1", "J2", "J3", "J4"])
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    if args.status:
        status()
        return
    if args.unseen:
        out = apply_unseen(args.prompt, args.limit)
    else:
        out = apply_batch(args.batch, args.prompt)
    if args.json:
        print(json.dumps(out))
    else:
        mode = out.get("mode", "batch")
        print(f"applied {mode} {out['batch']}")
        for pid, info in out["prompts"].items():
            extra = f", skip={info['skip_count']}" if "skip_count" in info else ""
            print(f"  {pid}: {info['count']} seeds{extra} -> {info['prompt']}")


if __name__ == "__main__":
    main()
