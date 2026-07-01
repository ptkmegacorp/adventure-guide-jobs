#!/usr/bin/env python3
"""Deterministic SearXNG candidate discovery with query diversity + CPU rerank."""
from __future__ import annotations
import argparse, json, re, subprocess, sys, urllib.parse, urllib.request
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

ROOT=Path(__file__).resolve().parent.parent
BLOCK={'indeed.com','linkedin.com','ziprecruiter.com','glassdoor.com','monster.com','simplyhired.com','talent.com','facebook.com','instagram.com','youtube.com','reddit.com','tripadvisor.com','getyourguide.com'}
ROLE_TERMS=['tour leader','trip leader','tour director','trip manager','travel director','destination host','driver guide','driver-guide','field instructor','program leader','expedition leader','guide','careers','employment','work with us','join our team','jobs']
MULTIDAY_TERMS=['multiday','multi-day','overnight','semester','summer program','small group','gap year','expedition','tour operator','travel program','walking holiday','cycling holiday']
REGION_TERMS={
 'J1':['new zealand','canada','usa','norway','global'],
 'J2':['new zealand','nz'],
 'J3':['usa','canada','gap year','student travel','summer'],
 'J4':['norway','scandinavia','nordic','iceland','sweden','finland'],
}

def format_searxng(query, data):
    rows=[]
    for i, page in enumerate((data.get('results') or [])[:10], start=1):
        title=page.get('title') or 'Untitled'
        url=page.get('url') or ''
        snippet=page.get('content') or page.get('snippet') or ''
        rows.append(f'{i}. [{title}]({url})\n{snippet}')
    if not rows:
        return f"No results found for '{query}'."
    return f"A web search for '{query}' found {len(rows)} results:\n\n## Web Results\n" + '\n\n'.join(rows)


def post_search(query):
    data=json.dumps({'query': query}).encode()
    req=urllib.request.Request('http://127.0.0.1:8001/search', data=data, headers={'Content-Type':'application/json'}, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            out=json.load(r)
        if not out.get('success'):
            raise RuntimeError(out.get('error'))
        return out.get('result','')
    except Exception:
        # Fallback: SearXNG directly if the LiteResearcher search_server is down.
        url='http://127.0.0.1:8888/search?' + urllib.parse.urlencode({'q':query,'format':'json'})
        with urllib.request.urlopen(url, timeout=60) as r:
            return format_searxng(query, json.load(r))

def parse_links(md):
    rows=[]
    parts=re.split(r'\n(?=\d+\. \[)', md)
    for part in parts:
        m=re.search(r'\d+\. \[([^\]]+)\]\(([^)]+)\)\n?(.*)', part, re.S)
        if not m: continue
        title,url,snippet=m.group(1).strip(),m.group(2).strip(),re.sub(r'\s+',' ',m.group(3)).strip()[:500]
        host=urlparse(url).netloc.lower().removeprefix('www.')
        if not host or any(host==b or host.endswith('.'+b) for b in BLOCK): continue
        rows.append({'title':title,'url':url,'host':host,'snippet':snippet})
    return rows

def tokens(s): return set(re.findall(r'[a-z0-9]+', s.lower()))
def jacc(a,b):
    A,B=tokens(a),tokens(b)
    return len(A&B)/max(1,len(A|B))

def expand_queries(pid, qs, max_queries=10):
    roles=['"tour leader"','"trip leader"','"tour director"','"trip manager"','"destination host"','"work with us"','careers']
    regions=REGION_TERMS.get(pid,[])
    pool=list(qs)
    for r in regions[:4]:
        for role in roles:
            pool.append(f'{role} {r} multiday travel careers -site:indeed.com -site:linkedin.com/jobs')
    picked=[]
    while pool and len(picked)<max_queries:
        if not picked:
            best=max(pool, key=lambda q: len(tokens(q)))
        else:
            best=max(pool, key=lambda q: min(1-jacc(q,p) for p in picked) + 0.05*len(tokens(q)))
        picked.append(best); pool.remove(best)
    return picked

def score_row(row, pid):
    text=f"{row['title']} {row['url']} {row['snippet']}".lower()
    score=0.0
    for t in ROLE_TERMS:
        if t in text: score+=3
    for t in MULTIDAY_TERMS:
        if t in text: score+=2
    for t in REGION_TERMS.get(pid,[]):
        if t in text: score+=2
    host=row['host']
    if any(x in host for x in ['careers','jobs']): score+=2
    if re.search(r'/careers?|/jobs?|work-with-us|employment|join', row['url'].lower()): score+=4
    if any(x in text for x in ['blog','review','best ','things to do','hotel management']): score-=4
    if any(x in host for x in ['backdoorjobs','coolworks','seasonaljobs']): score-=1
    return score

def update_registry(out_path: Path, source: str) -> str:
    proc = subprocess.run(
        [sys.executable, str(ROOT/'lib'/'update-candidates.py'), '--from-file', str(out_path), '--source-run', source],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    if proc.returncode != 0:
        return 'candidate registry update failed: ' + (proc.stderr or proc.stdout).strip()
    return (proc.stdout or '').strip()


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('id'); ap.add_argument('--queries'); ap.add_argument('--max-queries',type=int,default=10); ap.add_argument('--top-k',type=int,default=30); ap.add_argument('--no-expand',action='store_true'); ap.add_argument('--no-update',action='store_true', help='write candidates markdown only; do not update findings/candidates.json'); args=ap.parse_args()
    qfile=Path(args.queries) if args.queries else ROOT/'queries'/f'{args.id}.txt'
    for alt in [f'{args.id}-nordics.txt',f'{args.id}-us-ca.txt',f'{args.id}-nz.txt',f'{args.id}-global.txt']:
        if not qfile.exists() and (ROOT/'queries'/alt).exists(): qfile=ROOT/'queries'/alt
    qs=[l.strip() for l in qfile.read_text().splitlines() if l.strip() and not l.startswith('#')]
    search_qs=qs if args.no_expand else expand_queries(args.id, qs, args.max_queries)
    seen=set(); rows=[]; raw=[]
    for q in search_qs:
        res=post_search(q); raw.append((q,res))
        for row in parse_links(res):
            if row['host'] in seen: continue
            seen.add(row['host']); row['query']=q; row['score']=score_row(row,args.id); rows.append(row)
    rows=sorted(rows, key=lambda r:r['score'], reverse=True)
    outdir=ROOT/'candidates'; outdir.mkdir(exist_ok=True)
    stamp=datetime.now().strftime("%Y%m%d-%H%M%S")
    out=outdir/f'{args.id}-{stamp}.md'
    source=f'discovery-{args.id}-{stamp}'
    lines=[f'# Candidate discovery — {args.id}','',f'- **source:** `{source}`',f'- **queries:** `{qfile.relative_to(ROOT)}`',f'- **expanded_queries:** {len(search_qs)}','- **rerank:** CPU lexical rubric score','- **candidate_registry:** auto-update unless `--no-update`','', '## Reranked candidate URLs','']
    for row in rows[:args.top_k]:
        lines.append(f"- **{row['title']}** — {row['url']}  ")
        lines.append(f"  - score: `{row['score']:.1f}`; host: `{row['host']}`; query: `{row['query']}`")
        if row.get('snippet'): lines.append(f"  - snippet: {row['snippet'][:220]}")
    lines += ['', '## Search queries used', '', *[f'- {q}' for q in search_qs], '', '## Raw search excerpts', '']
    for q,res in raw:
        lines += [f'### {q}', '', res[:3000], '']
    out.write_text('\n'.join(lines), encoding='utf-8')
    print(out.relative_to(ROOT))
    if not args.no_update:
        msg=update_registry(out, source)
        if msg:
            print(msg)
if __name__=='__main__': main()
