#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re, urllib.request
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

ROOT=Path(__file__).resolve().parent.parent
DB=ROOT/'findings'/'candidates.json'
MASTER=ROOT/'findings'/'master.md'
QWEN='http://127.0.0.1:8093/v1/chat/completions'
MODEL='qwen3.5-4b-summary-local'

PROMPT='''Extract candidate employer records from the markdown evidence. Return ONLY JSON array.
Each object fields: company, region, primary_url, careers_url, role_titles(array), trip_type, hiring_signal, signal_strength(one of live|seasonal|careers|work-with-us|watchlist|inaccessible|unknown), fit(one of High|Medium|Low|Future|Watchlist), evidence, notes.
Include watchlist candidates if they clearly run multiday tours/programs even without live postings. Do not invent; use empty strings/arrays if unknown.'''

def load_db():
    if DB.exists(): return json.loads(DB.read_text())
    return {"version":1,"updated_at":None,"candidates":[]}

def save_db(db):
    DB.parent.mkdir(exist_ok=True)
    db['updated_at']=date.today().isoformat()
    DB.write_text(json.dumps(db, indent=2, ensure_ascii=False)+'\n')

def norm_company(s): return re.sub(r'[^a-z0-9]+',' ',(s or '').lower()).strip()
def host(u):
    try: return urlparse(u or '').netloc.lower().removeprefix('www.')
    except Exception: return ''

def key(rec):
    h=host(rec.get('primary_url') or rec.get('careers_url'))
    return h or norm_company(rec.get('company'))

def call_qwen(md):
    body=json.dumps({'model':MODEL,'messages':[{'role':'system','content':PROMPT},{'role':'user','content':md[:28000]}],'temperature':0.1,'max_tokens':2500}).encode()
    req=urllib.request.Request(QWEN,data=body,headers={'Content-Type':'application/json'},method='POST')
    with urllib.request.urlopen(req,timeout=360) as r: out=json.load(r)
    txt=(out['choices'][0]['message']['content'] or '').strip()
    txt=txt.replace('```json','').replace('```','').strip()
    l,r=txt.find('['),txt.rfind(']')
    if l>=0 and r>=0: txt=txt[l:r+1]
    return json.loads(txt)

def clean(rec, source):
    return {
        'company': str(rec.get('company','')).strip(),
        'region': str(rec.get('region','')).strip(),
        'primary_url': str(rec.get('primary_url','')).strip(),
        'careers_url': str(rec.get('careers_url','')).strip(),
        'role_titles': [str(x).strip() for x in rec.get('role_titles') or [] if str(x).strip()],
        'trip_type': str(rec.get('trip_type','')).strip(),
        'hiring_signal': str(rec.get('hiring_signal','')).strip(),
        'signal_strength': str(rec.get('signal_strength','unknown')).strip() or 'unknown',
        'fit': str(rec.get('fit','Watchlist')).strip() or 'Watchlist',
        'evidence': str(rec.get('evidence','')).strip()[:1000],
        'notes': str(rec.get('notes','')).strip(),
        'source_runs': [source],
        'last_seen': date.today().isoformat(),
    }

def merge(db, records):
    existing={key(r):r for r in db.get('candidates',[]) if key(r)}
    for rec in records:
        k=key(rec)
        if not k or not rec.get('company'): continue
        if k in existing:
            old=existing[k]
            for f in ['company','region','primary_url','careers_url','trip_type','hiring_signal','signal_strength','fit','evidence','notes']:
                if rec.get(f) and (not old.get(f) or len(str(rec.get(f)))>len(str(old.get(f)))): old[f]=rec[f]
            old['role_titles']=sorted(set((old.get('role_titles') or [])+(rec.get('role_titles') or [])))
            old['source_runs']=sorted(set((old.get('source_runs') or [])+(rec.get('source_runs') or [])))
            old['last_seen']=date.today().isoformat()
        else:
            db.setdefault('candidates',[]).append(rec); existing[k]=rec

def render(db):
    rows=db.get('candidates',[])
    def section(title, pred):
        out=[f'## {title}','', '| Company | Region | Signal | URL | Fit | Notes |','|---|---|---|---|---|---|']
        anyrow=False
        for r in sorted([x for x in rows if pred(x)], key=lambda x:(x.get('region',''),x.get('company',''))):
            url=r.get('careers_url') or r.get('primary_url') or ''
            notes=(r.get('notes') or r.get('evidence') or '')[:180].replace('\n',' ')
            out.append(f"| {r.get('company','')} | {r.get('region','')} | {r.get('hiring_signal','')} | {url} | {r.get('fit','')} | {notes} |")
            anyrow=True
        return '\n'.join(out+([''] if anyrow else ['| | | | | | |','']))
    text=['# Master employer list','', 'Generated from `findings/candidates.json`. Curate manually as needed.','', 'Core target: **multiday group travel leadership**; outdoor/adventure preferred but not required.','']
    text.append(section('High / Medium candidates', lambda r: r.get('fit') in ('High','Medium')))
    text.append(section('Watchlist candidates', lambda r: r.get('fit')=='Watchlist' or r.get('signal_strength') in ('watchlist','work-with-us','careers')))
    text.append(section('Future / Low / inaccessible', lambda r: r.get('fit') in ('Future','Low') or r.get('signal_strength')=='inaccessible'))
    MASTER.write_text('\n'.join(text), encoding='utf-8')

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--from-file', required=True); ap.add_argument('--source-run'); args=ap.parse_args()
    src=Path(args.from_file); md=src.read_text(encoding='utf-8', errors='replace')
    source=args.source_run or src.stem
    raw=call_qwen(md)
    records=[clean(r, source) for r in raw if isinstance(r,dict)]
    db=load_db(); merge(db,records); save_db(db); render(db)
    print(f'updated {DB.relative_to(ROOT)} with {len(records)} records; rendered {MASTER.relative_to(ROOT)}')
if __name__=='__main__': main()
