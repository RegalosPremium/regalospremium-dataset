#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,json,sqlite3,subprocess,re,unicodedata
from collections import Counter,defaultdict
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def slug(s):
 s=''.join(c for c in unicodedata.normalize('NFKD',s or '') if not unicodedata.combining(c)).lower()
 return re.sub(r'-+','-',re.sub(r'[^a-z0-9]+','-',s)).strip('-')

def mysql_rows(sql,args):
 cmd=['mariadb','--batch','--raw','--skip-column-names']
 if args.defaults_extra_file: cmd.append(f'--defaults-extra-file={args.defaults_extra_file}')
 if args.mysql_socket: cmd.append(f'--socket={args.mysql_socket}')
 if args.mysql_user: cmd.append(f'--user={args.mysql_user}')
 cmd.append(args.database)
 p=subprocess.run(cmd,input=sql,text=True,capture_output=True,check=True)
 return [line.rstrip('\n').split('\t') for line in p.stdout.splitlines()]

def main():
 ap=argparse.ArgumentParser(description='Build Regalos Premium ecosystem SQLite mirror')
 ap.add_argument('--database',required=True)
 ap.add_argument('--mysql-socket')
 ap.add_argument('--mysql-user',default='root')
 ap.add_argument('--defaults-extra-file')
 ap.add_argument('--shop-id',type=int,default=1); ap.add_argument('--lang-id',type=int,default=1)
 ap.add_argument('--output',default=str(ROOT/'var/ecosystem.db'))
 a=ap.parse_args(); out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True)
 if out.exists(): out.unlink()
 db=sqlite3.connect(out); db.executescript((ROOT/'schema/ecosystem.sqlite.sql').read_text(encoding='utf-8'))
 cat_sql=f"""SELECT c.id_category,c.id_parent,c.active,c.level_depth,COALESCE(cl.name,''),COALESCE(cl.link_rewrite,'') FROM ps_category c LEFT JOIN ps_category_lang cl ON cl.id_category=c.id_category AND cl.id_shop={a.shop_id} AND cl.id_lang={a.lang_id} ORDER BY c.id_category"""
 categories=mysql_rows(cat_sql,a)
 for r in categories:
  cid,parent,active,depth,name,rewrite=r; url=f'https://regalospremium.cl/{rewrite}/' if rewrite and rewrite not in ('inicio','home') else 'https://regalospremium.cl/'
  db.execute('INSERT INTO categories VALUES(?,?,?,?,?,?,?,?)',(int(cid),int(parent),int(active),int(depth),name,rewrite,url,'PRESENT'))
 prod_sql=f"""SELECT p.id_product,COALESCE(p.reference,''),COALESCE(pl.name,''),COALESCE(pl.link_rewrite,''),ps.active,ps.indexed,ps.visibility,ps.available_for_order,ps.show_price,COALESCE(ps.id_category_default,0),COALESCE(cl.name,''),COALESCE(cl.link_rewrite,''),ps.date_upd FROM ps_product p JOIN ps_product_shop ps ON ps.id_product=p.id_product AND ps.id_shop={a.shop_id} LEFT JOIN ps_product_lang pl ON pl.id_product=p.id_product AND pl.id_shop={a.shop_id} AND pl.id_lang={a.lang_id} LEFT JOIN ps_category_lang cl ON cl.id_category=ps.id_category_default AND cl.id_shop={a.shop_id} AND cl.id_lang={a.lang_id} ORDER BY p.id_product"""
 products=mysql_rows(prod_sql,a)
 known_categories={int(r[0]) for r in categories}
 orphan_category_ids=sorted({int(r[9]) for r in products if int(r[9]) and int(r[9]) not in known_categories})
 for cid in orphan_category_ids:
  db.execute('INSERT INTO categories VALUES(?,?,?,?,?,?,?,?)',(cid,0,0,0,f'[MISSING CATEGORY {cid}]','',None,'MISSING'))
 for r in products:
  pid,ref,name,rewrite,active,indexed,vis,afo,show,catid,catname,catrewrite,dateupd=r
  if int(catid) in orphan_category_ids:
   db.execute('INSERT INTO prestashop_anomalies(anomaly_type,object_id,related_id,details) VALUES(?,?,?,?)',('MISSING_DEFAULT_CATEGORY',int(pid),int(catid),'Default category referenced by product is absent from ps_category'))
  cand=f'https://regalospremium.cl/{catrewrite}/{rewrite}.html' if rewrite and catrewrite and catrewrite not in ('inicio','home') else (f'https://regalospremium.cl/{rewrite}.html' if rewrite else '')
  db.execute('INSERT INTO products VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(int(pid),f'product:{pid}',ref,name,rewrite,int(active),int(indexed),vis,int(afo),int(show),int(catid) or None,catname,cand,dateupd))
 pc=mysql_rows('SELECT id_product,id_category FROM ps_category_product ORDER BY id_product,id_category',a)
 existing_products={int(r[0]) for r in products}
 existing_categories={r[0] for r in db.execute('SELECT category_id FROM categories')}
 valid_pc=[]
 for x,y in pc:
  pid,cid=int(x),int(y)
  if pid not in existing_products:
   db.execute('INSERT INTO prestashop_anomalies(anomaly_type,object_id,related_id,details) VALUES(?,?,?,?)',('ORPHAN_PRODUCT_CATEGORY_LINK',pid,cid,'ps_category_product references missing product'))
   continue
  if cid not in existing_categories:
   db.execute('INSERT OR IGNORE INTO categories VALUES(?,?,?,?,?,?,?,?)',(cid,0,0,0,f'[MISSING CATEGORY {cid}]','',None,'MISSING'))
   existing_categories.add(cid)
   db.execute('INSERT INTO prestashop_anomalies(anomaly_type,object_id,related_id,details) VALUES(?,?,?,?)',('MISSING_CATEGORY_LINK',pid,cid,'ps_category_product references missing category'))
  valid_pc.append((pid,cid))
 db.executemany('INSERT OR IGNORE INTO product_categories VALUES(?,?)',valid_pc)
 with (ROOT/'data/productos.csv').open(encoding='utf-8-sig',newline='') as f: gh=list(csv.DictReader(f))
 for r in gh:
  pid=int(r['product_id']); fam=r['familia']; fk=f'family:{slug(fam)}' if fam else None
  db.execute('INSERT INTO taxonomy_products VALUES(?,?,?,?,?,?,?,?,?)',(pid,r['macroarea'],fam,fk,r['url'],r['categoria_actual'],r['seo_landing_candidate'],r['classification_confidence'],r['classification_status']))
  db.execute('INSERT INTO url_registry VALUES(?,?,?,?,?,1)',(r['url'],'GITHUB','PRODUCT',f'product:{pid}','CANONICAL'))
 with (ROOT/'data/ads/ads_campaign_blueprint.csv').open(encoding='utf-8',newline='') as f: bp=list(csv.DictReader(f))
 for r in bp:
  db.execute('INSERT INTO ads_blueprint VALUES(?,?,?,?,?,?,?,?,?,?,NULL,NULL)',(r['entity_key'],r['campaign'],r['ad_group'],r['intent_class'],r['macroarea'],r['familia'],r['theme'],int(r['keyword_count']),r['landing_source'],r['activation_state']))
 with (ROOT/'data/ads/ads_intent_mapping.csv').open(encoding='utf-8',newline='') as f: kw=list(csv.DictReader(f))
 for r in kw:
  ek=None
  if r['intent_class']=='PRODUCTO' and r['familia']: ek=f"family:{slug(r['familia'])}"
  elif r['intent_class']=='USO_CAMPAÑA' and r['intent_theme']: ek=f"intent:{slug(r['intent_theme'])}"
  db.execute('INSERT INTO ads_keywords(keyword,match_type,legacy_ad_group,intent_class,macroarea,family,theme,entity_key,historical_urls,normalized_urls,classification_confidence,impressions_max,clicks_max,conversions_max) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(r['keyword'],r['match_type'],r['ad_group'],r['intent_class'],r['macroarea'],r['familia'],r['intent_theme'],ek,r['historical_urls'],r['normalized_urls'],r['classification_confidence'],int(r['impressions_max']),int(r['clicks_max']),float(r['conversions_max'])))
  for u in [x.strip() for x in r['historical_urls'].split('|') if x.strip()]:
   db.execute('INSERT OR IGNORE INTO url_registry VALUES(?,?,?,?,?,0)',(u,'ADS_HISTORY','KEYWORD',ek or 'unmapped',r['url_statuses']))
 # Family -> PrestaShop default-category candidates based on active mapped products.
 q='''SELECT t.family_entity_key,t.family,p.default_category_id,p.default_category_name,c.category_url,COUNT(*) n FROM taxonomy_products t JOIN products p USING(product_id) LEFT JOIN categories c ON c.category_id=p.default_category_id WHERE p.active=1 AND t.family_entity_key IS NOT NULL GROUP BY t.family_entity_key,t.family,p.default_category_id,p.default_category_name,c.category_url'''
 famrows=db.execute(q).fetchall(); totals=defaultdict(int)
 for ek,fam,cid,cname,curl,n in famrows: totals[ek]+=n
 by=defaultdict(list)
 for row in famrows: by[row[0]].append(row)
 for ek,rows in by.items():
  maxn=max(r[-1] for r in rows)
  for _,fam,cid,cname,curl,n in rows:
   db.execute('INSERT INTO family_category_candidates VALUES(?,?,?,?,?,?,?,?)',(ek,fam,cid or 0,cname or '',curl,n,n/totals[ek],1 if n==maxn else 0))
 # Resolve blueprint only when a dominant family category is unique and >50% representative.
 for ek, in db.execute("SELECT entity_key FROM ads_blueprint WHERE intent_class='PRODUCTO'").fetchall():
  cands=db.execute('SELECT category_url,share FROM family_category_candidates WHERE family_entity_key=? AND is_dominant=1 ORDER BY share DESC',(ek,)).fetchall()
  if len(cands)==1 and cands[0][0] and cands[0][1]>0.5:
   db.execute('UPDATE ads_blueprint SET resolved_url=?,resolution_method=? WHERE entity_key=?',(cands[0][0],'PRESTASHOP_DOMINANT_CATEGORY',ek))
 # Resolve still-unresolved product families from dominant historical Ads destination only with strong evidence.
 hist=defaultdict(Counter)
 for r in kw:
  if r['intent_class']!='PRODUCTO' or not r['familia']: continue
  ek=f"family:{slug(r['familia'])}"
  for u in [x.strip() for x in r['normalized_urls'].split('|') if x.strip()]:
   if u.rstrip('/')=='https://regalospremium.cl' or '/busqueda?' in u or 'index.php?' in u or '?' in u or 'bamboohttps' in u: continue
   hist[ek][u]+=1
 for ek,counter in hist.items():
  row=db.execute('SELECT resolved_url FROM ads_blueprint WHERE entity_key=?',(ek,)).fetchone()
  if not row or row[0] or not counter: continue
  total=sum(counter.values()); top_url,top_n=counter.most_common(1)[0]
  if total>=20 and top_n/total>=0.60:
   db.execute('UPDATE ads_blueprint SET resolved_url=?,resolution_method=? WHERE entity_key=?',(top_url,'ADS_HISTORICAL_DOMINANT',ek))

 counts={'products_total':len(products),'products_active':sum(int(r[4]) for r in products),'github_products':len(gh),'categories':db.execute('SELECT COUNT(*) FROM categories').fetchone()[0],'orphan_category_ids':orphan_category_ids,'prestashop_anomalies':db.execute('SELECT COUNT(*) FROM prestashop_anomalies').fetchone()[0],'ads_keywords':len(kw),'ads_blueprint':len(bp)}
 missing_ps=[int(r['product_id']) for r in gh if not db.execute('SELECT 1 FROM products WHERE product_id=?',(int(r['product_id']),)).fetchone()]
 active_ids={r[0] for r in db.execute('SELECT product_id FROM products WHERE active=1')}; gh_ids={int(r['product_id']) for r in gh}
 missing_gh=sorted(active_ids-gh_ids)
 status='PASS' if not missing_ps and not missing_gh else 'DRIFT'
 db.execute('INSERT INTO sync_runs(started_at,source,products_total,products_active,github_products,status,notes) VALUES(?,?,?,?,?,?,?)',(datetime.now(timezone.utc).isoformat(),'PRESTASHOP+GITHUB+ADS',counts['products_total'],counts['products_active'],counts['github_products'],status,json.dumps({'github_not_prestashop':missing_ps,'active_prestashop_not_github':missing_gh})))
 for k,v in counts.items(): db.execute('INSERT INTO meta VALUES(?,?)',(k,str(v)))
 db.commit()
 print(json.dumps({**counts,'status':status,'github_not_prestashop':missing_ps,'active_prestashop_not_github':missing_gh,'db':str(out)},ensure_ascii=False,indent=2))
 db.close()
if __name__=='__main__': main()
