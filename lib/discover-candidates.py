#!/usr/bin/env python3
"""Deterministic SearXNG candidate discovery for adventure-guide-jobs."""
from __future__ import annotations
import argparse, json, re, urllib.request
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

ROOT=Path(__file__).resolve().parent.parent
BLOCK={'indeed.com','linkedin.com','ziprecruiter.com','glassdoor.com','monster.com','simplyhired.com','talent.com','facebook.com','instagram.com','youtube.com','reddit.com'}

def post_search(query):
    data=json.dumps({'query': query}).encode()
    req=urllib.request.Request('http://127.0.0.1:8001/search', data=data, headers={'Content-Type':'application/json'}, method='POST')
    with urllib.request.urlopen(req, timeout=60) as r:
        out=json.load(r)
    if not out.get('success'):
        raise RuntimeError(out.get('error'))
    return out.get('result','')

def links(md):
    for title,url in re.findall(r'\d+\. \[([^\]]+)\]\(([^)]+)\)', md):
        host=urlparse(url).netloc.lower().removeprefix('www.')
        if not host or any(host==b or host.endswith('.'+b) for b in BLOCK):
            continue
        yield title.strip(), url.strip(), host

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('id'); ap.add_argument('--queries'); args=ap.parse_args()
    qfile=Path(args.queries) if args.queries else ROOT/'queries'/f'{args.id}.txt'
    if not qfile.exists() and args.id=='J4': qfile=ROOT/'queries'/'J4-nordics.txt'
    if not qfile.exists() and args.id=='J3': qfile=ROOT/'queries'/'J3-us-ca.txt'
    if not qfile.exists() and args.id=='J2': qfile=ROOT/'queries'/'J2-nz.txt'
    if not qfile.exists() and args.id=='J1': qfile=ROOT/'queries'/'J1-global.txt'
    qs=[l.strip() for l in qfile.read_text().splitlines() if l.strip() and not l.startswith('#')]
    seen=set(); rows=[]; raw=[]
    for q in qs:
        res=post_search(q); raw.append((q,res))
        for title,url,host in links(res):
            if host in seen: continue
            seen.add(host); rows.append((title,url,host,q))
    outdir=ROOT/'candidates'; outdir.mkdir(exist_ok=True)
    out=outdir/f'{args.id}-{datetime.now().strftime("%Y%m%d-%H%M%S")}.md'
    lines=[f'# Candidate discovery — {args.id}','',f'- **queries:** `{qfile.relative_to(ROOT)}`','', '## Candidate URLs','']
    for title,url,host,q in rows[:40]:
        lines.append(f'- **{title}** — {url}  '); lines.append(f'  - host: `{host}`; query: `{q}`')
    lines += ['', '## Raw search excerpts', '']
    for q,res in raw:
        lines += [f'### {q}', '', res[:3000], '']
    out.write_text('\n'.join(lines), encoding='utf-8')
    print(out.relative_to(ROOT))
if __name__=='__main__': main()
