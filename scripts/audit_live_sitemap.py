#!/usr/bin/env python3
import csv,json,urllib.request
from pathlib import Path
from urllib.parse import urlsplit
from xml.etree import ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
BASE='https://regalospremium.cl'
UA={'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) Firefox/155.0','Accept':'application/xml,text/xml,*/*'}
NS={'s':'http://www.sitemaps.org/schemas/sitemap/0.9'}

def fetch(url):
 req=urllib.request.Request(url,headers=UA)
 with urllib.request.urlopen(req,timeout=30) as r:
  return r.status,dict(r.headers),r.read()

def slug_from_url(url):
 leaf=urlsplit(url).path.rstrip('/').rsplit('/',1)[-1]
 return leaf[:-5] if leaf.endswith('.html') else ''

_,_,index_xml=fetch(BASE+'/1_index_sitemap.xml')
idx=ET.fromstring(index_xml)
children=[x.text.strip() for x in idx.findall('s:sitemap/s:loc',NS)]
live=[]; child_meta=[]
for child in children:
 status,headers,data=fetch(child)
 root=ET.fromstring(data)
 urls=[x.text.strip() for x in root.findall('s:url/s:loc',NS)]
 live.extend(urls)
 child_meta.append({'url':child,'http_status':status,'last_modified':headers.get('Last-Modified'),'url_count':len(urls)})
with (ROOT/'data/productos.csv').open(encoding='utf-8-sig',newline='') as f:
 products=list(csv.DictReader(f))
live_slugs={slug_from_url(u) for u in live if slug_from_url(u)}
missing=[]
for p in products:
 slug=slug_from_url(p['url'])
 if slug and slug not in live_slugs:
  missing.append({'product_id':p['product_id'],'reference':p['reference'],'nombre':p['nombre'],'slug':slug,'canonical_url':p['url']})
report={'index_url':BASE+'/1_index_sitemap.xml','child_sitemaps':child_meta,'live_urls':len(live),'live_unique_urls':len(set(live)),'catalog_products':len(products),'catalog_unique_urls':len({p['url'] for p in products}),'covered_by_slug':len(products)-len(missing),'missing_by_slug':len(missing)}
outdir=ROOT/'reports/sitemap'; outdir.mkdir(parents=True,exist_ok=True)
(outdir/'sitemap_audit_latest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding='utf-8')
with (outdir/'missing_live_sitemap_products.csv').open('w',encoding='utf-8',newline='') as f:
 w=csv.DictWriter(f,fieldnames=['product_id','reference','nombre','slug','canonical_url']); w.writeheader(); w.writerows(missing)
print(json.dumps(report,ensure_ascii=False,indent=2))
