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
SIGNALS={'live','seasonal','careers','work-with-us','watchlist','inaccessible','unknown'}
FITS={'High','Medium','Low','Future','Watchlist'}

PROMPT='''Extract candidate employer records from the markdown evidence. Return ONLY JSON array.
Each object MUST have: company, region, primary_url, careers_url, role_titles(array), trip_type, hiring_signal, signal_strength, fit, evidence, notes.
Allowed signal_strength: live, seasonal, careers, work-with-us, watchlist, inaccessible, unknown.
Allowed fit: High, Medium, Low, Future, Watchlist.
Include watchlist candidates if they clearly run multiday tours/programs even without live postings. Do not invent; use empty strings/arrays if unknown.'''
RETRY='''Your previous output failed schema validation. Return ONLY a valid JSON array. Fix enum values and include a non-empty company for each record. No markdown.'''

def load_db():
    return json.loads(DB.read_text()) if DB.exists() else {"version":1,"updated_at":None,"candidates":[]}
def save_db(db):
    DB.parent.mkdir(exist_ok=True); db['updated_at']=date.today().isoformat(); DB.write_text(json.dumps(db, indent=2, ensure_ascii=False)+'\n')
def norm_company(s): return re.sub(r'[^a-z0-9]+',' ',(s or '').lower()).strip()
def host(u):
    try: return urlparse(u or '').netloc.lower().removeprefix('www.')
    except Exception: return ''
def key(rec): return host(rec.get('primary_url') or rec.get('careers_url')) or norm_company(rec.get('company'))

def extract_json(txt):
    txt=(txt or '').strip().replace('```json','').replace('```','').strip()
    l,r=txt.find('['),txt.rfind(']')
    if l>=0 and r>=0: txt=txt[l:r+1]
    return json.loads(txt)

def call_qwen(md, extra=''):
    msgs=[{'role':'system','content':PROMPT},{'role':'user','content':(extra+'\n\n'+md[:28000]).strip()}]
    body=json.dumps({'model':MODEL,'messages':msgs,'temperature':0.1,'max_tokens':2500}).encode()
    req=urllib.request.Request(QWEN,data=body,headers={'Content-Type':'application/json'},method='POST')
    with urllib.request.urlopen(req,timeout=360) as r: out=json.load(r)
    return out['choices'][0]['message']['content'] or ''

def validate_and_clean(raw, source):
    records=[]; errors=[]
    if not isinstance(raw,list): return [], ['top-level JSON is not an array']
    for i,rec in enumerate(raw):
        if not isinstance(rec,dict): errors.append(f'{i}: not object'); continue
        company=str(rec.get('company','')).strip()
        if not company: errors.append(f'{i}: missing company'); continue
        sig=str(rec.get('signal_strength','unknown')).strip().lower() or 'unknown'
        if sig not in SIGNALS:
            if 'work' in sig: sig='work-with-us'
            elif 'career' in sig: sig='careers'
            elif 'live' in sig or 'posting' in sig: sig='live'
            elif 'inaccess' in sig or 'blocked' in sig: sig='inaccessible'
            else: sig='unknown'
        fit=str(rec.get('fit','Watchlist')).strip().title() or 'Watchlist'
        if fit not in FITS: fit='Watchlist'
        evidence=str(rec.get('evidence','')).strip()[:1000]
        # Keep weak records, but flag them in notes rather than dropping useful watchlist info.
        notes=str(rec.get('notes','')).strip()
        if not evidence and sig not in {'inaccessible','watchlist'}:
            notes=(notes+'; weak/no direct evidence').strip('; ')
        records.append({
            'company': company,
            'region': str(rec.get('region','')).strip(),
            'primary_url': str(rec.get('primary_url','')).strip(),
            'careers_url': str(rec.get('careers_url','')).strip(),
            'role_titles': [str(x).strip() for x in rec.get('role_titles') or [] if str(x).strip()],
            'trip_type': str(rec.get('trip_type','')).strip(),
            'hiring_signal': str(rec.get('hiring_signal') or sig).strip(),
            'signal_strength': sig,
            'fit': fit,
            'evidence': evidence,
            'notes': notes,
            'source_runs': [source],
            'last_seen': date.today().isoformat(),
        })
    return records, errors

def candidate_score(r):
    score=0
    score += {'live':50,'seasonal':42,'work-with-us':30,'careers':25,'watchlist':15,'unknown':5,'inaccessible':0}.get(r.get('signal_strength'),0)
    score += {'High':35,'Medium':22,'Watchlist':10,'Future':8,'Low':0}.get(r.get('fit'),0)
    text=' '.join([r.get('trip_type',''), r.get('evidence',''), r.get('notes',''), ' '.join(r.get('role_titles') or [])]).lower()
    for t in ['multiday','multi-day','overnight','semester','4-week','10-week','small-group','group travel','trip leader','tour leader','program instructor','field instructor','driver-guide']:
        if t in text: score += 4
    if r.get('careers_url'): score += 4
    return score

def apply_listwise_ranking(db):
    rows=db.get('candidates',[])
    for r in rows: r['rank_score']=candidate_score(r)
    for rank,r in enumerate(sorted(rows,key=lambda x:x.get('rank_score',0), reverse=True), start=1):
        r['rank']=rank
        r['rank_rationale']=f"signal={r.get('signal_strength')}; fit={r.get('fit')}; score={r.get('rank_score')}"

def fallback_records_from_markdown(md, source):
    records=[]
    # Candidate discovery markdown: bullet title/url plus score/snippet metadata.
    pat=re.compile(r"- \*\*([^*]+)\*\* — (https?://\S+)\s*\n\s*- score: `?([^`;]+).*?(?:\n\s*- snippet: ([^\n]+))?", re.S)
    for m in pat.finditer(md):
        title,url,score,snippet=m.group(1).strip(),m.group(2).strip(),m.group(3).strip(),(m.group(4) or '').strip()
        company=re.sub(r'\s*[-|].*$', '', title).strip()
        company=re.sub(r'^(Become an?|Careers? at|Travel Careers|Find a New Career in)\s+', '', company, flags=re.I).strip()
        text=f'{title} {url} {snippet}'.lower()
        sig='careers' if any(x in text for x in ['career','employment','job','work with us']) else 'watchlist'
        fit='Medium' if any(x in text for x in ['tour leader','trip leader','guide','multiday','multi-day','small-group']) else 'Watchlist'
        records.append(clean_record({
            'company': company,
            'region': '',
            'primary_url': url,
            'careers_url': url if sig=='careers' else '',
            'role_titles': [],
            'trip_type': '',
            'hiring_signal': sig,
            'signal_strength': sig,
            'fit': fit,
            'evidence': snippet,
            'notes': f'Fallback extraction from candidate discovery result; score={score}',
        }, source))
    return records


def clean_record(rec, source):
    records, _ = validate_and_clean([rec], source)
    return records[0] if records else {}


def merge(db, records):
    existing={key(r):r for r in db.get('candidates',[]) if key(r)}
    for rec in records:
        k=key(rec)
        if not k: continue
        if k in existing:
            old=existing[k]
            for f in ['company','region','primary_url','careers_url','trip_type','hiring_signal','signal_strength','fit','evidence','notes']:
                if rec.get(f) and (not old.get(f) or candidate_score(rec) >= candidate_score(old) or len(str(rec.get(f)))>len(str(old.get(f)))): old[f]=rec[f]
            old['role_titles']=sorted(set((old.get('role_titles') or [])+(rec.get('role_titles') or [])))
            old['source_runs']=sorted(set((old.get('source_runs') or [])+(rec.get('source_runs') or [])))
            old['last_seen']=date.today().isoformat()
        else:
            db.setdefault('candidates',[]).append(rec); existing[k]=rec
    apply_listwise_ranking(db)

def render(db):
    rows=sorted(db.get('candidates',[]), key=lambda x:x.get('rank',9999))
    def section(title, pred):
        out=[f'## {title}','', '| Rank | Company | Region | Signal | URL | Fit | Notes |','|---:|---|---|---|---|---|---|']
        matched=[r for r in rows if pred(r)]
        if not matched: return '\n'.join(out+['| | | | | | | |',''])
        for r in matched:
            url=r.get('careers_url') or r.get('primary_url') or ''
            notes=(r.get('notes') or r.get('evidence') or r.get('rank_rationale') or '')[:180].replace('\n',' ')
            out.append(f"| {r.get('rank','')} | {r.get('company','')} | {r.get('region','')} | {r.get('hiring_signal','')} | {url} | {r.get('fit','')} | {notes} |")
        return '\n'.join(out+[''])
    text=['# Master employer list','', 'Generated from `findings/candidates.json`. Curate manually as needed.','', 'Core target: **multiday group travel leadership**; outdoor/adventure preferred but not required.','', 'Ranking is a deterministic rubric over signal strength, fit, role/trip evidence, and careers URL presence.','']
    text.append(section('High / Medium candidates', lambda r: r.get('fit') in ('High','Medium')))
    text.append(section('Watchlist candidates', lambda r: r.get('fit')=='Watchlist' or r.get('signal_strength') in ('watchlist','work-with-us','careers')))
    text.append(section('Future / Low / inaccessible', lambda r: r.get('fit') in ('Future','Low') or r.get('signal_strength')=='inaccessible'))
    MASTER.write_text('\n'.join(text), encoding='utf-8')

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--from-file', required=True); ap.add_argument('--source-run'); args=ap.parse_args()
    src=Path(args.from_file); md=src.read_text(encoding='utf-8', errors='replace'); source=args.source_run or src.stem
    try:
        raw=extract_json(call_qwen(md)); records, errors=validate_and_clean(raw, source)
        if errors and not records: raise ValueError('; '.join(errors))
    except Exception as e:
        try:
            raw=extract_json(call_qwen(md, RETRY+f'\nError: {e}')); records, errors=validate_and_clean(raw, source)
        except Exception as e2:
            records=fallback_records_from_markdown(md, source)
            errors=[f'Qwen unavailable or invalid JSON; used deterministic markdown fallback: {e2}']
    db=load_db(); merge(db,records); save_db(db); render(db)
    print(f'updated {DB.relative_to(ROOT)} with {len(records)} records; rendered {MASTER.relative_to(ROOT)}')
    if errors: print('schema_warnings: '+ '; '.join(errors[:5]))
if __name__=='__main__': main()
