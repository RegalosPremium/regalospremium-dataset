#!/usr/bin/env python3
import csv,re,unicodedata,json
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def slug(s):
 s=''.join(c for c in unicodedata.normalize('NFKD',s) if not unicodedata.combining(c)).lower()
 return re.sub(r'-+','-',re.sub(r'[^a-z0-9]+','-',s)).strip('-')

with (ROOT/'data/ads/ads_intent_mapping.csv').open(encoding='utf-8',newline='') as f:
 rows=list(csv.DictReader(f))
with (ROOT/'data/ads/ads_landing_decisions.csv').open(encoding='utf-8',newline='') as f:
 decisions={r['entity_key']:r for r in csv.DictReader(f)}
prod=Counter((r['macroarea'],r['familia']) for r in rows if r['intent_class']=='PRODUCTO')
tax=json.loads((ROOT/'data/categorias.json').read_text(encoding='utf-8'))
all_pairs=[(x['macroarea'],fam) for x in tax['taxonomia'] for fam in x['familias']]
themes=Counter((r['macroarea'],r['intent_theme']) for r in rows if r['intent_class']=='USO_CAMPAÑA')
out=[]
for macro,fam in sorted(all_pairs):
 n=prod.get((macro,fam),0); ek=f'family:{slug(fam)}'; d=decisions.get(ek,{})
 state=d.get('activation_state') or ('WAIT_PRESTASHOP_URL' if n else 'HOLD_NO_HISTORICAL_KEYWORDS')
 out.append({'campaign':f'RP | Search | {macro}','ad_group':fam,'entity_key':ek,'intent_class':'PRODUCTO','macroarea':macro,'familia':fam,'theme':'','keyword_count':n,'landing_source':'DECISION_REGISTRY' if d else 'PRESTASHOP_FAMILY','activation_state':state,'resolved_url':d.get('resolved_url',''),'resolution_method':d.get('resolution_method','')})
for (macro,theme),n in sorted(themes.items(),key=lambda x:(x[0][1].lower(),x[0][0].lower())):
 if not theme: continue
 out.append({'campaign':'RP | Search | Intención','ad_group':theme,'entity_key':f'intent:{slug(theme)}','intent_class':'USO_CAMPAÑA','macroarea':macro,'familia':'','theme':theme,'keyword_count':n,'landing_source':'PRESTASHOP_LANDING','activation_state':'WAIT_PRESTASHOP_URL','resolved_url':'','resolution_method':''})
fields=['campaign','ad_group','entity_key','intent_class','macroarea','familia','theme','keyword_count','landing_source','activation_state','resolved_url','resolution_method']
with (ROOT/'data/ads/ads_campaign_blueprint.csv').open('w',encoding='utf-8',newline='') as f:
 w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(out)
product=[x for x in out if x['intent_class']=='PRODUCTO']
print('blueprint_rows',len(out),'product_adgroups',len(product),'ready',sum(x['activation_state']=='READY_URL' for x in product),'hold',sum(x['activation_state'].startswith('HOLD_') for x in product),'campaigns',len({x['campaign'] for x in out}))
for c in sorted({x['campaign'] for x in out}): print(c,sum(x['campaign']==c for x in out))
