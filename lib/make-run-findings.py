#!/usr/bin/env python3
"""Create a per-run findings note from extraction, review, and visit evidence."""
from __future__ import annotations
import argparse, json, re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parent.parent
REG=ROOT/'runs/registry.json'
FINDINGS=ROOT/'findings'

def now(): return datetime.now(timezone.utc).astimezone().isoformat(timespec='seconds')
def load(): return json.loads(REG.read_text())
def save(d): REG.write_text(json.dumps(d, indent=2)+'\n')
def find_run(d, rid):
    for r in d.get('runs',[]):
        if r.get('run_id')==rid: return r
    raise SystemExit(f'run not found: {rid}')
def strip_heading(text):
    return re.sub(r'^# .+?\n+', '', text.strip(), count=1, flags=re.S)
def visit_evidence(log_text, limit=12):
    out=[]
    pat=re.compile(r"\[visit_result\] The useful information in (\S+) for user goal (.+?) as follows:\s*\n\s*Evidence in page:\s*\n(.+?)(?=\n\[turn\]|\n\[model\]|\n\[search\]|\n\[visit\]|\n---\n|\Z)", re.S)
    for m in pat.finditer(log_text):
        ev=' '.join(m.group(3).strip().split())[:900]
        if ev:
            out.append((m.group(1), ev))
        if len(out)>=limit: break
    return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--run-id', required=True); args=ap.parse_args()
    d=load(); r=find_run(d,args.run_id)
    FINDINGS.mkdir(exist_ok=True)
    log_text=(ROOT/r['log']).read_text(encoding='utf-8', errors='replace') if r.get('log') else ''
    extracted=''
    if r.get('extracted_path') and (ROOT/r['extracted_path']).exists():
        extracted=strip_heading((ROOT/r['extracted_path']).read_text(encoding='utf-8', errors='replace'))
    review=''
    if r.get('review_path') and (ROOT/r['review_path']).exists():
        review=strip_heading((ROOT/r['review_path']).read_text(encoding='utf-8', errors='replace'))
    evidence=visit_evidence(log_text)
    salvage=''
    if r.get('salvage_path') and (ROOT/r['salvage_path']).exists():
        salvage=strip_heading((ROOT/r['salvage_path']).read_text(encoding='utf-8', errors='replace'))
    salvage_status=r.get('salvage_status') or ''
    if salvage_status == 'ok':
        status='salvaged'
    elif int(r.get('answer_chars') or 0)>=100:
        status='useful'
    elif salvage_status == 'partial' or evidence or review:
        status='partial'
    else:
        status='failed'
    out=FINDINGS/f"{r['run_id']}.md"
    lines=[f"# Run findings — {r['run_id']}", '', f"- **prompt:** {r.get('prompt_id')}", f"- **status:** {status}", f"- **log:** `{r.get('log','')}`", f"- **review:** `{r.get('review_path','')}`", f"- **extracted:** `{r.get('extracted_path','')}`", f"- **salvage:** `{r.get('salvage_path','')}`", f"- **salvage_status:** {salvage_status or '—'}", f"- **salvage_employers:** {r.get('salvage_employer_count','—')}", f"- **created_at:** {now()}", '']
    if salvage:
        lines += ['## Salvaged findings (primary)', '', salvage, '']
    if extracted:
        lines += ['## Extracted LR final answer (audit)', '', extracted, '']
    if review:
        lines += ['## Run review', '', review, '']
    if evidence:
        lines += ['## Visit evidence snippets', '']
        for url, ev in evidence:
            lines += [f"### {url}", '', ev, '']
    out.write_text('\n'.join(lines).rstrip()+'\n', encoding='utf-8')
    rel=str(out.relative_to(ROOT))
    r['findings_path']=rel; r['findings_status']=status; r['findings_written_at']=now()
    ps=d.setdefault('prompts',{}).setdefault(r.get('prompt_id','?'),{})
    ps['last_findings']=rel; ps['last_findings_status']=status
    save(d)
    print(rel)
if __name__=='__main__': main()
