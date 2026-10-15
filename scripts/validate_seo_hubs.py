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

owners={(r['macroarea'],r['familia']):r['owner_url'] for r in coverage}
full=read('data/seo/seo_hub_catalog_coverage.csv')
if len(full)!=len(products) or len({r['product_id'] for r in full})!=len(full):
    errors.append('full product coverage count or duplicate ID')
if {r['product_id'] for r in full}!=set(by_id): errors.append('full coverage IDs differ from catalog')
for r in full:
    p=by_id.get(r['product_id'],{})
    if any(r[k]!=p.get(k) for k in ('reference','macroarea','familia')) or r['product_url']!=p.get('url'):
        errors.append(f"product coverage drift {r['product_id']}")
    if r['owner_url']!=owners.get((r['macroarea'],r['familia'])):
        errors.append(f"product owner drift {r['product_id']}")
exceptions=read('data/seo/seo_hub_editorial_exceptions.csv')
exception_map={(r['product_id'],r['hub_url']):r for r in exceptions}
if len(exception_map)!=len(exceptions): errors.append('duplicate editorial exception')
used_exceptions=set()
family_links=read('data/seo/seo_hub_family_links.csv')
if len(family_links)!=len(tax_pairs) or {(r['macroarea'],r['familia']) for r in family_links}!=tax_pairs:
    errors.append('family navigation coverage differs from taxonomy')
for r in family_links:
    p=by_id.get(r['representative_product_id'],{})
    if (p.get('macroarea'),p.get('familia'))!=(r['macroarea'],r['familia']) or p.get('url')!=r['product_url']:
        errors.append(f"family representative drift {r['familia']}")
    if r['owner_url']!=owners.get((r['macroarea'],r['familia'])):
        errors.append(f"family link owner drift {r['familia']}")
selection=read('data/seo/seo_hub_product_selection.csv')
selected={}
for r in selection:
    selected.setdefault(r['hub_url'],[]).append(r['product_id'])
    p=by_id.get(r['product_id'],{})
    if r['status']!='ACTIVE' or r['hub_category']!={CORP:'140',PUB:'141'}.get(r['hub_url']):
        errors.append(f"invalid selected status/category {r['product_id']}")
    if r['familia']!=p.get('familia'): errors.append(f"selection family drift {r['product_id']}")
    owner=owners.get((p.get('macroarea'),p.get('familia')))
    if owner!=r['hub_url']:
        key=(r['product_id'],r['hub_url']);e=exception_map.get(key,{})
        if e.get('family_owner_url')!=owner or not e.get('reason','').strip():
            errors.append(f"undocumented editorial owner exception {r['product_id']}")
        used_exceptions.add(key)
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

if used_exceptions!=set(exception_map): errors.append('unused editorial exception')

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
