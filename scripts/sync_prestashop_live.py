#!/usr/bin/env python3
from __future__ import annotations
import argparse,base64,json,os,sqlite3,time
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request,urlopen
ROOT=Path(__file__).resolve().parents[1]
FIELDS=['id','reference','active','date_upd','link_rewrite','id_category_default','indexed','visibility','available_for_order','show_price','name']

def get_key(path):
 k=os.getenv('PRESTASHOP_WS_KEY','').strip()
 if not k and path:
  k=Path(path).read_text(encoding='utf-8').strip()
 if not k: raise SystemExit('Set PRESTASHOP_WS_KEY or --key-file')
 return k

def fetch_batch(base,key,offset,limit):
 q=urlencode({'url':'products','display':'['+','.join(FIELDS)+']','limit':f'{offset},{limit}','output_format':'JSON'})
 url=base.rstrip('/')+'/webservice/dispatcher.php?'+q
 token=base64.b64encode((key+':').encode()).decode()
 req=Request(url,headers={'Authorization':'Basic '+token,'Accept':'application/json','User-Agent':'RegalosPremium-Ecosystem/1.0'})
 with urlopen(req,timeout=30) as r:
  if r.status!=200: raise RuntimeError(f'HTTP {r.status}')
  return json.loads(r.read().decode('utf-8')).get('products',[])

def main():
 ap=argparse.ArgumentParser(description='Read-only live PrestaShop product sync into ecosystem SQLite')
 ap.add_argument('--base-url',default='https://regalospremium.cl')
 ap.add_argument('--key-file',default=str(ROOT/'config/prestashop-webservice.key'))
 ap.add_argument('--db',default=str(ROOT/'var/ecosystem.db'))
 ap.add_argument('--batch-size',type=int,default=250)
 ap.add_argument('--report',default=str(ROOT/'reports/prestashop/live_sync_latest.json'))
 a=ap.parse_args(); key=get_key(a.key_file)
 products=[]; offset=0
 while True:
  batch=fetch_batch(a.base_url,key,offset,a.batch_size)
  products.extend(batch)
  if len(batch)<a.batch_size: break
  offset+=len(batch); time.sleep(.15)
 ids=[int(x['id']) for x in products]
 if len(ids)!=len(set(ids)): raise SystemExit('Duplicate product IDs from Webservice pagination')
 c=sqlite3.connect(a.db); c.execute('PRAGMA foreign_keys=ON')
 before={r[0] for r in c.execute('SELECT product_id FROM products WHERE active=1')}
 new_products=[]; unknown_categories=[]
 for x in products:
  pid=int(x['id']); catid=int(x.get('id_category_default') or 0) or None
  cat=c.execute('SELECT name,link_rewrite,category_url FROM categories WHERE category_id=?',(catid,)).fetchone() if catid else None
  if catid and not cat:
   c.execute('INSERT OR IGNORE INTO categories(category_id,parent_id,active,level_depth,name,link_rewrite,category_url,source_status) VALUES(?,?,?,?,?,?,?,?)',(catid,0,0,0,f'[LIVE UNKNOWN CATEGORY {catid}]','',None,'LIVE_UNKNOWN'))
   c.execute('INSERT INTO prestashop_anomalies(anomaly_type,object_id,related_id,details) VALUES(?,?,?,?)',('LIVE_UNKNOWN_CATEGORY',pid,catid,'Webservice product references category absent from last DB snapshot'))
   unknown_categories.append(catid); cat=None
  cname=cat[0] if cat else ''
  crewrite=cat[1] if cat else ''
  rewrite=x.get('link_rewrite') or ''
  cand=f'https://regalospremium.cl/{crewrite}/{rewrite}.html' if crewrite and rewrite else (f'https://regalospremium.cl/{rewrite}.html' if rewrite else '')
  row=c.execute('SELECT 1 FROM products WHERE product_id=?',(pid,)).fetchone()
  vals=(x.get('reference') or '',x.get('name') or '',rewrite,int(x.get('active') or 0),int(x.get('indexed') or 0),x.get('visibility') or '',int(x.get('available_for_order') or 0),int(x.get('show_price') or 0),catid,cname,cand,x.get('date_upd') or '',pid)
  if row:
   c.execute('UPDATE products SET reference=?,name=?,link_rewrite=?,active=?,indexed=?,visibility=?,available_for_order=?,show_price=?,default_category_id=?,default_category_name=?,prestashop_candidate_url=?,date_upd=? WHERE product_id=?',vals)
  else:
   c.execute('INSERT INTO products(product_id,entity_key,reference,name,link_rewrite,active,indexed,visibility,available_for_order,show_price,default_category_id,default_category_name,prestashop_candidate_url,date_upd) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(pid,f'product:{pid}',*vals[:-1]))
   new_products.append(pid)
 live_ids=set(ids); active_ids={r[0] for r in c.execute('SELECT product_id FROM products WHERE active=1')}
 gh_ids={r[0] for r in c.execute('SELECT product_id FROM taxonomy_products')}
 missing_gh=sorted(active_ids-gh_ids); inactive_but_github=sorted(gh_ids-active_ids)
 after=active_ids
 activated=sorted(after-before); deactivated=sorted(before-after)
 status='PASS' if not missing_gh and not inactive_but_github else 'DRIFT'
 notes={'api_products':len(products),'new_products':new_products,'activated':activated,'deactivated':deactivated,'active_prestashop_not_github':missing_gh,'github_not_active_prestashop':inactive_but_github,'unknown_category_ids':sorted(set(unknown_categories))}
 c.execute('INSERT INTO sync_runs(started_at,source,products_total,products_active,github_products,status,notes) VALUES(?,?,?,?,?,?,?)',(datetime.now(timezone.utc).isoformat(),'PRESTASHOP_WEBSERVICE',len(products),len(active_ids),len(gh_ids),status,json.dumps(notes)))
 c.commit(); c.close()
 report={'status':status,'fetched_products':len(products),'active_products':len(active_ids),'github_products':len(gh_ids),**notes}
 rp=Path(a.report);rp.parent.mkdir(parents=True,exist_ok=True);rp.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
