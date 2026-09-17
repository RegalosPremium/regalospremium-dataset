#!/usr/bin/env python3
import csv,json,sys
from pathlib import Path
from urllib.parse import urlsplit
ROOT=Path(__file__).resolve().parents[1]
errors=[]
with (ROOT/'data/categorias.json').open(encoding='utf-8') as f: tax=json.load(f)
pairs={(x['macroarea'],fam) for x in tax['taxonomia'] for fam in x['familias']}
with (ROOT/'data/ads/ads_intent_mapping.csv').open(encoding='utf-8',newline='') as f: rows=list(csv.DictReader(f))
with (ROOT/'data/ads/ads_group_mapping.csv').open(encoding='utf-8',newline='') as f: groups=list(csv.DictReader(f))
with (ROOT/'data/ads/ads_url_inventory.csv').open(encoding='utf-8',newline='') as f: urls=list(csv.DictReader(f))
with (ROOT/'data/ads/ads_campaign_blueprint.csv').open(encoding='utf-8',newline='') as f: blueprint=list(csv.DictReader(f))
allowed={'PRODUCTO','USO_CAMPAÑA','DESCARTAR'}
for i,r in enumerate(rows,2):
 if r['intent_class'] not in allowed: errors.append(f'row {i}: invalid intent_class')
 if r['intent_class']=='PRODUCTO':
  if not r['familia']: errors.append(f'row {i}: PRODUCTO without family')
  elif (r['macroarea'],r['familia']) not in pairs: errors.append(f"row {i}: invalid taxonomy pair {r['macroarea']} / {r['familia']}")
 if r['intent_class']=='DESCARTAR' and r['familia']: errors.append(f'row {i}: DESCARTAR has family')
 for u in [x.strip() for x in r['normalized_urls'].split('|') if x.strip()]:
  q=urlsplit(u)
  if q.scheme!='https' or q.netloc!='regalospremium.cl': errors.append(f'row {i}: bad normalized URL {u}')
if len({(r['keyword'].lower(),r['match_type'],r['ad_group']) for r in rows})!=len(rows): errors.append('duplicate keyword key')
if len(groups)!=len({r['ad_group'] for r in rows}): errors.append('group summary mismatch')
summary=json.loads((ROOT/'reports/ads/ads_mapping_summary.json').read_text(encoding='utf-8'))
if summary['unique_keyword_keys']!=len(rows): errors.append('summary keyword count mismatch')
if summary['unique_historical_urls']!=len(urls): errors.append('summary URL count mismatch')
blue_families={(r['macroarea'],r['familia']) for r in blueprint if r['intent_class']=='PRODUCTO'}
if blue_families!=pairs: errors.append('blueprint does not cover all taxonomy families')
if len(blue_families)!=tax['familias_reales']: errors.append('blueprint family count mismatch')
print(f"ads_keywords={len(rows)} groups={len(groups)} urls={len(urls)} product={sum(r['intent_class']=='PRODUCTO' for r in rows)} campaign={sum(r['intent_class']=='USO_CAMPAÑA' for r in rows)} discard={sum(r['intent_class']=='DESCARTAR' for r in rows)} blueprint={len(blueprint)} families={len(blue_families)}")
for e in errors: print('ERROR:',e,file=sys.stderr)
sys.exit(1 if errors else 0)
