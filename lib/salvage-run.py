#!/usr/bin/env python3
"""Salvage a LiteResearcher trajectory by re-browsing visited URLs and summarizing with Qwen sidecar."""
from __future__ import annotations
import argparse, json, re, urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parent.parent
REG=ROOT/'runs/registry.json'
FINDINGS=ROOT/'findings'
BROWSE='http://127.0.0.1:8002/browse'
QWEN='http://127.0.0.1:8093/v1/chat/completions'
MODEL='qwen3.5-4b-summary-local'

def now(): return datetime.now(timezone.utc).astimezone().isoformat(timespec='seconds')
def load(): return json.loads(REG.read_text())
def save(d): REG.write_text(json.dumps(d, indent=2)+'\n')
def find_run(d,rid):
    for r in d.get('runs',[]):
        if r.get('run_id')==rid: return r
    raise SystemExit(f'run not found: {rid}')

def visited_urls(log_text:str)->list[str]:
    urls=[]
    for m in re.finditer(r'\[visit\]\s*(\{.+)', log_text):
        chunk=m.group(1).split('\n',1)[0]
        try:
            payload=json.loads(chunk); u=payload.get('url') or []
            if isinstance(u,str): u=[u]
            urls += [x for x in u if isinstance(x,str)]
            continue
        except Exception:
            pass
        for u in re.findall(r'https?://[^\s"\]\},]+', chunk):
            urls.append(u.rstrip('",'))
    for u in re.findall(r'^- (https?://\S+)', log_text, re.M):
        urls.append(u)
    seen=set(); out=[]
    for u in urls:
        u=u.rstrip(').,')
        if u not in seen:
            seen.add(u); out.append(u)
    return out

def post_json(url:str, payload:dict, timeout:int=300)->dict:
    data=json.dumps(payload).encode()
    req=urllib.request.Request(url, data=data, headers={'Content-Type':'application/json'}, method='POST')
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)

def browse(url:str, goal:str)->str:
    out=post_json(BROWSE, {'url': url, 'goal': goal}, timeout=360)
    if not out.get('success'): return f'ERROR browsing {url}: {out.get("error")}'
    return out.get('result','')

def count_employers(summary: str) -> int:
    if not summary.strip():
        return 0
    n = len(re.findall(r"^#{1,4}\s+\d+\.\s+", summary, re.M))
    if n:
        return n
    n = len(re.findall(r"^\*\s+\*\*Company:\*\*", summary, re.M))
    if n:
        return n
    return max(0, 1 if len(summary.strip()) >= 200 else 0)


def salvage_quality(summary: str) -> tuple[str, int]:
    summary = (summary or "").strip()
    count = count_employers(summary)
    if count >= 1 and len(summary) >= 200:
        return "ok", count
    if summary:
        return "partial", count
    return "empty", 0


def qwen_summary(run_id:str, evidence:str)->str:
    system='''You turn web evidence into concise adventure job findings. Be factual. Do not invent. If evidence is weak, say so.'''
    user=f'''Run {run_id}: summarize this evidence for multiday adventure guide/trip leader employer research.

For each company/page with useful evidence, include:
- company
- country/region
- possible role titles, broadly including tour leader, trip leader, tour director, trip manager, destination host, driver-guide, guide, expedition leader, program leader, or field instructor
- careers/jobs/work-with-us URL
- multiday tour/program signal
- hiring signal: live posting | careers page | work-with-us page | watchlist/no live posting | inaccessible
- fit: High/Medium/Low/Future/Watchlist
- one evidence quote or paraphrase tied to the page

If no live job is found, still preserve useful candidate/contact/careers-page evidence. The main target is multiday group travel leadership, not only outdoor/adventure guiding.

Evidence:
{evidence[:24000]}'''
    out=post_json(QWEN, {'model':MODEL,'messages':[{'role':'system','content':system},{'role':'user','content':user}], 'temperature':0.2, 'max_tokens':2500}, timeout=360)
    return (out.get('choices',[{}])[0].get('message',{}).get('content') or '').strip()

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--run-id', required=True); ap.add_argument('--limit', type=int, default=10); args=ap.parse_args()
    d=load(); r=find_run(d,args.run_id)
    log_text=(ROOT/r['log']).read_text(encoding='utf-8', errors='replace')
    urls=visited_urls(log_text)[:args.limit]
    if not urls: raise SystemExit('no visited urls found')
    goal='Extract hiring/careers/job evidence for multiday group travel leadership roles. Include tour leader, trip leader, tour director, trip manager, destination host, driver-guide, guide, expedition leader, program leader, or field instructor signals. Preserve watchlist candidates if the company clearly runs multiday tours/programs even without live postings. Include job titles, careers URLs, region, requirements, season, and whether evidence is a live posting, careers page, work-with-us page, or no signal.'
    chunks=[]
    for u in urls:
        chunks.append(f'## {u}\n\n{browse(u, goal)[:5000]}')
    evidence='\n\n'.join(chunks)
    summary=qwen_summary(args.run_id, evidence)
    FINDINGS.mkdir(exist_ok=True)
    out=FINDINGS/f'{args.run_id}-salvage.md'
    content=f'''# Salvaged findings — {args.run_id}

- **prompt:** {r.get('prompt_id')}
- **source log:** `{r.get('log')}`
- **created_at:** {now()}
- **method:** Re-browsed {len(urls)} visited URLs with browser_server and summarized with Qwen sidecar.

## Qwen salvage summary

{summary or '_No summary produced._'}

## Re-browsed evidence

{evidence}
'''
    out.write_text(content, encoding='utf-8')
    rel=str(out.relative_to(ROOT))
    status, emp_count = salvage_quality(summary or '')
    r['salvage_path']=rel
    r['salvage_status']=status
    r['salvage_employer_count']=emp_count
    r['salvaged_at']=now()
    ps=d.setdefault('prompts',{}).setdefault(r.get('prompt_id','?'),{})
    ps['last_salvage']=rel
    ps['last_salvage_status']=status
    ps['salvage_employer_count']=emp_count
    save(d)
    print(rel)
    print(f"salvage_status={status} employers={emp_count}", file=__import__('sys').stderr)
if __name__=='__main__': main()
