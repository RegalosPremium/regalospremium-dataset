#!/usr/bin/env python3
from __future__ import annotations
import csv,ssl,sys,time
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError
ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'data/ads/ads_url_inventory.csv'
OUT=ROOT/'reports/ads/ads_url_http_20260917.csv'
UA='Mozilla/5.0 (compatible; RegalosPremium-QA/1.0; +https://regalospremium.cl/)'
ctx=ssl.create_default_context()
def check(row):
 u=row['historical_url']
 if row['status']=='INVALID': return {**row,'http_code':'','effective_url':'','live_status':'SKIP_INVALID','error':''}
 try:
  req=Request(u,headers={'User-Agent':UA},method='GET')
  with urlopen(req,timeout=10,context=ctx) as r:
   code=getattr(r,'status',200); eff=r.geturl()
   return {**row,'http_code':str(code),'effective_url':eff,'live_status':'LIVE' if 200<=code<400 else 'HTTP_ERROR','error':''}
 except HTTPError as e:
  status='INCONCLUSIVE_SERVER_LOOP' if e.code==508 else ('DEAD_404' if e.code==404 else 'HTTP_ERROR')
  return {**row,'http_code':str(e.code),'effective_url':e.geturl() or u,'live_status':status,'error':str(e.reason)}
 except Exception as e:
  return {**row,'http_code':'','effective_url':'','live_status':'INCONCLUSIVE_NETWORK','error':type(e).__name__+': '+str(e)[:180]}
with SRC.open(encoding='utf-8',newline='') as f: rows=list(csv.DictReader(f))
results=[]
with ThreadPoolExecutor(max_workers=5) as ex:
 futs={ex.submit(check,r):r for r in rows}
 for fut in as_completed(futs): results.append(fut.result())
results.sort(key=lambda x:(x['live_status'],x['historical_url']))
fields=list(results[0].keys())
OUT.parent.mkdir(parents=True,exist_ok=True)
with OUT.open('w',encoding='utf-8',newline='') as f:
 w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(results)
from collections import Counter
print('checked',len(results),dict(Counter(r['live_status'] for r in results)))
for r in results:
 if r['live_status']!='LIVE': print(r['live_status'],r['http_code'],r['historical_url'],r['error'])
