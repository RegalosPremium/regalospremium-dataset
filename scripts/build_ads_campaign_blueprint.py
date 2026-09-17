#!/usr/bin/env python3
import csv,re,unicodedata,json
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def slug(s):
 s=''.join(c for c in unicodedata.normalize('NFKD',s) if not unicodedata.combining(c)).lower()
 return re.sub(r'-+','-',re.sub(r'[^a-z0-9]+','-',s)).strip('-')
with (ROOT/'data/ads/ads_intent_mapping.csv').open(encoding='utf-8',newline='') as f: rows=list(csv.DictReader(f))
prod=Counter((r['macroarea'],r['familia']) for r in rows if r['intent_class']=='PRODUCTO')
tax=json.loads((ROOT/'data/categorias.json').read_text(encoding='utf-8'))
all_pairs=[(x['macroarea'],fam) for x in tax['taxonomia'] for fam in x['familias']]
themes=Counter((r['macroarea'],r['intent_theme']) for r in rows if r['intent_class']=='USO_CAMPAÑA')
out=[]
for macro,fam in sorted(all_pairs):
 n=prod.get((macro,fam),0)
 state='WAIT_PRESTASHOP_URL' if n else 'HOLD_NO_HISTORICAL_KEYWORDS'
 out.append({'campaign':f'RP | Search | {macro}','ad_group':fam,'entity_key':f'family:{slug(fam)}','intent_class':'PRODUCTO','macroarea':macro,'familia':fam,'theme':'','keyword_count':n,'landing_source':'PRESTASHOP_FAMILY','activation_state':state})
for (macro,theme),n in sorted(themes.items(),key=lambda x:(x[0][1].lower(),x[0][0].lower())):
 if not theme: continue
 out.append({'campaign':'RP | Search | Intención','ad_group':theme,'entity_key':f'intent:{slug(theme)}','intent_class':'USO_CAMPAÑA','macroarea':macro,'familia':'','theme':theme,'keyword_count':n,'landing_source':'PRESTASHOP_LANDING','activation_state':'WAIT_PRESTASHOP_URL'})
fields=list(out[0])
with (ROOT/'data/ads/ads_campaign_blueprint.csv').open('w',encoding='utf-8',newline='') as f:
 w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(out)
print('blueprint_rows',len(out),'product_adgroups',sum(x['intent_class']=='PRODUCTO' for x in out),'intent_adgroups',sum(x['intent_class']=='USO_CAMPAÑA' for x in out),'campaigns',len({x['campaign'] for x in out}))
for c in sorted({x['campaign'] for x in out}): print(c,sum(x['campaign']==c for x in out))
