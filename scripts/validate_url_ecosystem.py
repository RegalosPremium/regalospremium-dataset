#!/usr/bin/env python3
import csv, collections, sys
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

ROOT=Path(__file__).resolve().parents[1]
HOST='regalospremium.cl'
errors=[]

def read(name):
    with (ROOT/name).open(encoding='utf-8-sig',newline='') as f:
        return list(csv.DictReader(f))

def good_url(value):
    p=urlsplit(value)
    return p.scheme=='https' and p.netloc==HOST and bool(p.path)

products=read(Path('data/productos.csv'))
by_id={r['product_id']:r for r in products}
by_url=collections.defaultdict(list)
for r in products:
    by_url[r['url']].append(r)
actual={u:{r['product_id'] for r in rs} for u,rs in by_url.items() if len(rs)>1}

registry=read(Path('data/url_duplicates.csv'))
seen_ids=set()
open_registered={}
for r in registry:
    did=r['duplicate_id']
    if did in seen_ids:
        errors.append(f'duplicate duplicate_id: {did}')
    seen_ids.add(did)
    ids={r['product_id_a'],r['product_id_b']}
    status=r['status']
    if status not in {'HOLD','SCHEDULED','RESOLVED'}:
        errors.append(f'{did}: invalid status {status}')
    if not good_url(r['current_url']):
        errors.append(f'{did}: invalid historical URL')
    if status in {'HOLD','SCHEDULED'}:
        open_registered[r['current_url']]=ids
        if actual.get(r['current_url']) != ids:
            errors.append(f'{did}: open registry != productos.csv')
    else:
        ua=r.get('resolved_url_a','').strip()
        ub=r.get('resolved_url_b','').strip()
        if not good_url(ua) or not good_url(ub) or ua==ub:
            errors.append(f'{did}: invalid resolved URL pair')
        if by_id.get(r['product_id_a'],{}).get('url')!=ua:
            errors.append(f'{did}: product A resolution differs from catalog')
        if by_id.get(r['product_id_b'],{}).get('url')!=ub:
            errors.append(f'{did}: product B resolution differs from catalog')
        try:
            date.fromisoformat(r.get('resolved_date',''))
        except ValueError:
            errors.append(f'{did}: invalid resolved_date')
if open_registered != actual:
    errors.append('open duplicate registry does not exactly match catalog duplicates')

queue=read(Path('data/url_changes.csv'))
change_ids=set()
for r in queue:
    cid=r['change_id']
    if cid in change_ids:
        errors.append(f'duplicate change_id: {cid}')
    change_ids.add(cid)
    if r['product_id'] not in by_id:
        errors.append(f'{cid}: unknown product_id {r["product_id"]}')
    if not good_url(r['old_url']) or not good_url(r['new_url']):
        errors.append(f'{cid}: invalid host/scheme')
    if r['old_url']==r['new_url']:
        errors.append(f'{cid}: old_url == new_url')
    if r['status'] not in {'READY','APPLIED','HOLD','FAILED'}:
        errors.append(f'{cid}: invalid status {r["status"]}')
    if r['effective_date']:
        try:
            date.fromisoformat(r['effective_date'])
        except ValueError:
            errors.append(f'{cid}: invalid effective_date')

print(f'products={len(products)} duplicates={len(actual)} registry={len(registry)} resolved={sum(r["status"]=="RESOLVED" for r in registry)} url_changes={len(queue)}')
for e in errors:
    print('ERROR:',e,file=sys.stderr)
sys.exit(1 if errors else 0)
