#!/usr/bin/env python3
from pathlib import Path
from urllib.parse import urlsplit
import csv, json, sys

ROOT=Path(__file__).resolve().parents[1]
CORP='https://regalospremium.cl/regalos-corporativos/'
PUB='https://regalospremium.cl/regalos-publicitarios/'
OWNERS={CORP,PUB}
errors=[]

def read(path):
    with (ROOT/path).open(encoding='utf-8-sig',newline='') as f:
        return list(csv.DictReader(f))

products=read('data/productos.csv')
by_id={r['product_id']:r for r in products}
tax=json.loads((ROOT/'data/categorias.json').read_text(encoding='utf-8'))
tax_pairs={(a['macroarea'],f) for a in tax['taxonomia'] for f in a['familias']}

coverage=read('data/seo/seo_hub_family_coverage.csv')
coverage_pairs=[(r['macroarea'],r['familia']) for r in coverage]
if len(coverage_pairs)!=len(set(coverage_pairs)):
    errors.append('duplicate family coverage row')
if set(coverage_pairs)!=tax_pairs:
    errors.append('family coverage differs from taxonomy')
if any(r['owner_url'] not in OWNERS or r['status']!='ACTIVE' for r in coverage):
    errors.append('invalid family owner or status')

selection=read('data/seo/seo_hub_product_selection.csv')
selected={}
for r in selection:
    selected.setdefault(r['hub_url'],[]).append(r['product_id'])
    if r['product_id'] not in by_id:
        errors.append(f'unknown selected product {r["product_id"]}')
    elif by_id[r['product_id']]['reference']!=r['reference']:
        errors.append(f'selection reference drift {r["product_id"]}')
if set(selected)!=OWNERS:
    errors.append('selection does not contain both hubs')
for owner in OWNERS:
    ids=selected.get(owner,[])
    if len(ids)!=12 or len(set(ids))!=12:
        errors.append(f'{owner}: expected 12 unique products')
if set(selected.get(CORP,[])) & set(selected.get(PUB,[])):
    errors.append('product overlap between hubs')

intent=read('data/seo/seo_intent_hubs_20261004.csv')
intent_map={}
for r in intent:
    q=r['query'].casefold().strip()
    if q in intent_map:
        errors.append(f'duplicate intent query {q}')
    intent_map[q]=r['owner_url']
    if r['owner_url'] not in OWNERS or r['status']!='ACTIVE':
        errors.append(f'invalid intent owner/status {q}')

generic=read('data/ads/ads_generic_keywords.csv')
generic_queries={r['keyword'].casefold().strip() for r in generic}
if set(intent_map)!=generic_queries:
    errors.append('SEO intent registry does not exactly cover generic Ads queries')
for r in generic:
    q=r['keyword'].casefold().strip()
    if r['final_url']!=intent_map.get(q):
        errors.append(f'generic Ads destination differs for {q}')

decisions={r['entity_key']:r for r in read('data/ads/ads_landing_decisions.csv')}
blueprint={r['entity_key']:r for r in read('data/ads/ads_campaign_blueprint.csv')}
required={
'intent:generico-corporativo':CORP,
'intent:regalos-corporativos':CORP,
'intent:regalos-publicitarios':PUB,
'intent:merchandising-corporativo':PUB,
}
for key,url in required.items():
    d=decisions.get(key); b=blueprint.get(key)
    if not d or not b:
        errors.append(f'missing canonical intent {key}')
        continue
    if d['resolved_url']!=url or b['resolved_url']!=url:
        errors.append(f'canonical intent destination differs {key}')
    if d['activation_state']!='READY_URL' or b['activation_state']!='READY_URL':
        errors.append(f'canonical intent is not READY {key}')

dsa=read('data/ads/ads_dsa_targets.csv')
dsa_urls={r['url'] for r in dsa if r['status']=='READY'}
if not OWNERS.issubset(dsa_urls):
    errors.append('DSA does not contain both generic hubs')
if 'https://regalospremium.cl/' in dsa_urls:
    errors.append('DSA still assigns generic intent to home')
for u in dsa_urls:
    p=urlsplit(u)
    if p.scheme!='https' or p.netloc!='regalospremium.cl':
        errors.append(f'invalid DSA URL {u}')

print(f'families={len(coverage_pairs)} family_owners={len(set(r["owner_url"] for r in coverage))} selected_corporate={len(selected.get(CORP,[]))} selected_publicitario={len(selected.get(PUB,[]))} overlap={len(set(selected.get(CORP,[])) & set(selected.get(PUB,[])))} generic_queries={len(generic_queries)} canonical_intents={len(required)}')
for e in errors:
    print('ERROR:',e,file=sys.stderr)
sys.exit(1 if errors else 0)
