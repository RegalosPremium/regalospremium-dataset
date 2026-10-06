#!/usr/bin/env python3
from pathlib import Path
import datetime,hashlib,json,re,requests

ROOT=Path(__file__).resolve().parents[1]
PARAMS=Path('/home/maxdaguzan/RegalosPremium_Carrusel_20260915/app/config/parameters.php')
BASE='https://regalospremium.cl'
STAMP=datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
BACK=Path('/home/maxdaguzan/RegalosPremium_Backups')/f'sitemap_riskfix_{STAMP}'
BACK.mkdir(parents=True,exist_ok=False)

text=PARAMS.read_text(encoding='utf-8')
m=re.search(r"'cookie_key'\s*=>\s*'([^']+)'",text)
if not m:raise RuntimeError('cookie_key unavailable')
token=hashlib.md5((m.group(1)+'gsitemap/cron').encode()).hexdigest()[:10]

for name in ('1_index_sitemap.xml','1_es_0_sitemap.xml'):
    r=requests.get(f'{BASE}/{name}',timeout=60)
    r.raise_for_status();(BACK/name).write_bytes(r.content)

r=requests.get(f'{BASE}/module/gsitemap/cron',params={'token':token,'id_shop':1},timeout=180,allow_redirects=True)
if r.status_code!=200:raise RuntimeError(f'gsitemap HTTP {r.status_code}')

after={}
for name in ('1_index_sitemap.xml','1_es_0_sitemap.xml'):
    q=requests.get(f'{BASE}/{name}',timeout=60,headers={'Cache-Control':'no-cache'})
    q.raise_for_status();after[name]={'http':q.status_code,'bytes':len(q.content),'last_modified':q.headers.get('Last-Modified','')}

report={'timestamp':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS','backup':str(BACK),'cron_http':r.status_code,'cron_final_url':r.url.split('?')[0],'sitemaps':after}
(ROOT/'reports/seo/sitemap_regeneration_20261006.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,ensure_ascii=False))
