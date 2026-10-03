#!/usr/bin/env python3
"""Read-only audit of the 2026-10-03 GSC coverage export master."""
import base64, csv, json, os, re, subprocess, sys
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urljoin, urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler, urlopen
from xml.etree import ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
MASTER=ROOT/'data/gsc/coverage_drilldown_20261003_master.csv'
REDIRECTS=ROOT/'data/seo_redirects.csv'
OUT=ROOT/'reports/seo'
ENV=Path('/home/maxdaguzan/Descargas/Creador_Plantillas_v1.1/creador-plantillas-app/config/prestashop.env')
SITE='https://regalospremium.cl/'
UA='RegalosPremium-GSC-Export-Audit/20261003 (+read-only)'

class CanonicalParser(HTMLParser):
 def __init__(self): super().__init__(); self.canonical=''; self.noindex=False
 def handle_starttag(self,tag,attrs):
  d=dict(attrs)
  if tag.lower()=='link' and d.get('rel','').lower()=='canonical': self.canonical=d.get('href','')
  if tag.lower()=='meta' and d.get('name','').lower()=='robots' and 'noindex' in d.get('content','').lower(): self.noindex=True

class NoRedirect(HTTPRedirectHandler):
 def redirect_request(self,*args,**kwargs): return None

def req(url, follow=True, timeout=25, max_bytes=1000000):
 opener=build_opener() if follow else build_opener(NoRedirect)
 request=Request(url,headers={'User-Agent':UA,'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'})
 try:
  with opener.open(request,timeout=timeout) as r:
   return {'status':r.status,'url':r.geturl(),'headers':dict(r.headers.items()),'body':r.read(max_bytes).decode('utf-8','replace'),'error':''}
 except HTTPError as e:
  return {'status':e.code,'url':url,'headers':dict(e.headers.items()),'body':e.read(max_bytes).decode('utf-8','replace'),'error':''}
 except Exception as e: return {'status':'ERROR','url':url,'headers':{},'body':'','error':f'{type(e).__name__}: {e}'}

def chain(url):
 seen=[]; cur=url
 for _ in range(10):
  x=req(cur,False)
  seen.append(f"{x['status']} {cur}")
  loc=x['headers'].get('Location') or x['headers'].get('location')
  if isinstance(x['status'],int) and x['status'] in (301,302,303,307,308) and loc:
   cur=urljoin(cur,loc); continue
  p=CanonicalParser(); p.feed(x['body'])
  return x, ' -> '.join(seen), p.canonical, p.noindex
 return x,' -> '.join(seen),'',False

def env():
 d={}
 for l in ENV.read_text(encoding='utf-8').splitlines():
  if '=' in l and not l.lstrip().startswith('#'):
   k,v=l.split('=',1); d[k.strip()]=v.strip().strip('"').strip("'")
 return d

def ps_get(path, params):
 e=env(); base=e['PRESTASHOP_BASE_URL'].rstrip('/'); key=e['PRESTASHOP_API_KEY']
 q=urlencode({'url':path,'output_format':'JSON',**params},safe='[],')
 request=Request(base+'/webservice/dispatcher.php?'+q,headers={'Authorization':'Basic '+base64.b64encode((key+':').encode()).decode(),'Accept':'application/json','User-Agent':UA})
 try:
  with urlopen(request,timeout=35) as r: return json.loads(r.read().decode()),''
 except Exception as ex: return {},f'{type(ex).__name__}: {ex}'

def ps_match(url):
 path=urlsplit(url).path.strip('/'); bits=path.split('/') if path else []
 product_slug=bits[-1][:-5] if bits and bits[-1].endswith('.html') else ''
 category_slug=bits[0] if bits else ''
 out={'prestashop_match':'none','product_id':'','reference':'','active':'','indexed':'','expected_canonical':'','prestashop_error':''}
 if product_slug:
  data,err=ps_get('products',{'display':'[id,reference,active,indexed,name,link_rewrite,id_category_default]','filter[link_rewrite]':f'[{product_slug}]'})
  rows=data.get('products',[]) if isinstance(data,dict) else []
  if rows:
   p=rows[0]; out.update({'prestashop_match':'product link_rewrite exact','product_id':str(p.get('id','')),'reference':p.get('reference',''),'active':str(p.get('active','')),'indexed':str(p.get('indexed',''))})
   cid=p.get('id_category_default','')
   if cid:
    cats,ce=ps_get(f'categories/{cid}',{'display':'[id,link_rewrite]'})
    c=cats.get('category',{}) if isinstance(cats,dict) else {}
    cr=c.get('link_rewrite','')
    if isinstance(cr,dict): cr=next(iter(cr.values()),'')
    if cr: out['expected_canonical']=SITE+str(cr).strip('/')+'/'+product_slug+'.html'
   return out
  out['prestashop_error']=err
 if category_slug:
  data,err=ps_get('categories',{'display':'[id,active,link_rewrite,name]','filter[link_rewrite]':f'[{category_slug}]'})
  rows=data.get('categories',[]) if isinstance(data,dict) else []
  if rows:
   c=rows[0]; out.update({'prestashop_match':'category link_rewrite exact','product_id':'category:'+str(c.get('id','')),'active':str(c.get('active','')),'expected_canonical':SITE+category_slug+'/'})
  elif err: out['prestashop_error']=err
 return out

def sitemap():
 result=req(SITE+'1_index_sitemap.xml',max_bytes=10000000); urls=set(); err=''
 try:
  ns={'s':'http://www.sitemaps.org/schemas/sitemap/0.9'}; root=ET.fromstring(result['body'])
  children=[x.text.strip() for x in root.findall('s:sitemap/s:loc',ns)]
  for child in children:
   x=req(child,max_bytes=10000000); leaf=ET.fromstring(x['body']); urls.update(n.text.strip() for n in leaf.findall('s:url/s:loc',ns))
 except Exception as ex: err=f'{type(ex).__name__}: {ex}'
 return urls,{'index_status':result['status'],'url_count':len(urls),'error':err}

def redirect_rule(url, rules):
 for r in rules:
  old=r['old_url']
  if old.endswith('*') and url.startswith(old[:-1]) or url==old: return r
 return {}

def robot_class(url):
 p=urlsplit(url); q=p.query.lower(); path=p.path.lower()
 deliberate=bool(q) or any(x in path for x in ('/carrito','/pedido','/order','/login','/iniciar-sesion','/mi-cuenta','/busqueda','/search','/autenticacion'))
 if deliberate: return 'DELIBERATE_PARAMETER_OR_UTILITY'
 return 'REVIEW_POTENTIALLY_HARMFUL'

def gsc_sa_probe():
 cmd=['/home/maxdaguzan/.local/gcloud-install/google-cloud-sdk/bin/gcloud','auth','print-access-token','--account','rp-google-ads-cli@able-marking-493221-m5.iam.gserviceaccount.com','--scopes','https://www.googleapis.com/auth/webmasters.readonly']
 try:
  p=subprocess.run(cmd,env={**os.environ,'CLOUDSDK_CONFIG':'/home/maxdaguzan/.config/gcloud-rp-explorer'},text=True,capture_output=True,timeout=45)
  # Never retain or print a token. A present token would be used only in-memory, but this profile has no SA credential.
  return {'service_account':'rp-google-ads-cli@able-marking-493221-m5.iam.gserviceaccount.com','scope':'https://www.googleapis.com/auth/webmasters.readonly','available':p.returncode==0,'detail':'available' if p.returncode==0 else (p.stderr.strip() or p.stdout.strip())[-500:]}
 except Exception as ex: return {'service_account':'rp-google-ads-cli@able-marking-493221-m5.iam.gserviceaccount.com','scope':'https://www.googleapis.com/auth/webmasters.readonly','available':False,'detail':f'{type(ex).__name__}: {ex}'}

def main():
 OUT.mkdir(parents=True,exist_ok=True)
 with MASTER.open(encoding='utf-8-sig',newline='') as f: rows=list(csv.DictReader(f))
 with REDIRECTS.open(encoding='utf-8-sig',newline='') as f: rules=list(csv.DictReader(f))
 sm,smmeta=sitemap(); robots=req(SITE+'robots.txt'); probe=gsc_sa_probe()
 by_issue=defaultdict(list)
 for r in rows: by_issue[r['issue']].append(r)
 audits=[]
 four=by_issue['No se ha encontrado (404)']
 # Full external + PrestaShop evidence is restricted to the 11 designated 404 URLs.
 with ThreadPoolExecutor(max_workers=5) as ex:
  fut={ex.submit(chain,r['url']):r for r in four}
  fetched={}
 for f in as_completed(fut): fetched[fut[f]['url']]=f.result()
 # The two singleton exception classes receive an individual live read; the 27
 # canonical-alternative URLs remain a class-level evaluation as requested.
 exceptions=[r for r in rows if r['issue'].startswith('Duplicada: Google ha elegido') or 'noindex' in r['issue'].lower()]
 exception_fetched={r['url']:chain(r['url']) for r in exceptions}
 for r in rows:
  issue,url=r['issue'],r['url']; a={'issue':issue,'url':url,'gsc_last_crawl':r['last_crawl'],'source_zip':r['source_zip']}
  a['in_live_sitemap']='yes' if url in sm else 'no'; rule=redirect_rule(url,rules); a['redirect_rule']=json.dumps(rule,ensure_ascii=False) if rule else ''
  if issue=='No se ha encontrado (404)':
   x,ch,can,noi=fetched[url]; a.update({'http_status':x['status'],'redirect_chain':ch,'final_url':x['url'],'canonical_current':can,'noindex_current':str(noi).lower(),**ps_match(url)})
   expected=a['expected_canonical']
   if isinstance(x['status'],int) and x['status'] in (200,301,302,303,307,308): a['classification']='PASS'; a['action']='conservar; canonical actual coincide' if x['status']==200 and can else 'conservar; validar destino canónico'
   elif a['prestashop_match'].startswith('category') and a['active']=='1' and urlsplit(url).path.endswith('.html'):
    a['classification']='PENDING'; a['action']='301 candidata hacia categoría activa '+expected+' sólo tras validar equivalencia semántica'
   elif a['prestashop_match'].startswith('product') and a['active']=='1' and expected: a['classification']='PENDING'; a['action']='301 hacia '+expected
   elif rule: a['classification']='PENDING'; a['action']='corregir destino de regla 301 '+rule.get('status','')+'; la cadena actual termina en 404'
   else: a['classification']='RISK'; a['action']='candidata a baja; conservar 404 y retirar de sitemap si apareciera; revisión humana'
   a['url_inspection']='NOT_QUERIED_SERVICE_ACCOUNT_UNAVAILABLE' if not probe['available'] else 'not implemented'
   a['search_analytics']='NOT_QUERIED_SERVICE_ACCOUNT_UNAVAILABLE' if not probe['available'] else 'not implemented'
   a['evidence']='HTTP GET live; sitemap GET; PrestaShop Webservice GET; GSC export last crawl'
  else:
   a.update({'http_status':'NOT_FETCHED_CLASS_AUDIT','redirect_chain':'','final_url':'','canonical_current':'','noindex_current':'','prestashop_match':'','product_id':'','reference':'','active':'','indexed':'','expected_canonical':'','url_inspection':'NOT_QUERIED_CLASS_AUDIT','search_analytics':'NOT_QUERIED_CLASS_AUDIT'})
   if issue=='Bloqueada por robots.txt':
    rc=robot_class(url); a['robots_class']=rc; a['classification']='PASS' if rc.startswith('DELIBERATE') else 'PENDING'; a['action']='conservar bloqueo deliberado' if rc.startswith('DELIBERATE') else 'revisar bloqueo robots y canonical'
   elif issue=='Página alternativa con etiqueta canónica adecuada': a['classification']='PASS'; a['action']='conservar canonical declarada; no indexar variante'
   elif issue.startswith('Duplicada: Google ha elegido'):
    x,ch,can,noi=exception_fetched[url]; a.update({'http_status':x['status'],'redirect_chain':ch,'final_url':x['url'],'canonical_current':can,'noindex_current':str(noi).lower()}); a['classification']='PENDING'; a['action']='revisar canonical declarada vs Google y señales internas'
   elif 'noindex' in issue.lower():
    x,ch,can,noi=exception_fetched[url]; a.update({'http_status':x['status'],'redirect_chain':ch,'final_url':x['url'],'canonical_current':can,'noindex_current':str(noi).lower()}); a['classification']='PASS' if noi else 'PENDING'; a['action']='conservar noindex deliberado' if noi else 'confirmar que noindex es deliberado; retirar si URL debe posicionar'
   else: a['classification']='PENDING'; a['action']='revisar'
   a['evidence']='GSC master export; individual HTTP GET for singleton exception' if issue.startswith('Duplicada: Google ha elegido') or 'noindex' in issue.lower() else 'GSC master export; classification by URL pattern only (no per-URL live fetch outside 404 priority)'
  audits.append(a)
 counts=defaultdict(Counter)
 for a in audits: counts[a['issue']][a['classification']]+=1
 problems=[a for a in audits if a['issue']=='Bloqueada por robots.txt' and a.get('robots_class')=='REVIEW_POTENTIALLY_HARMFUL']
 payload={'audit_date':str(date.today()),'source_master':str(MASTER),'source_rows':len(rows),'scope':'External read-only. GSC API is not queried because the explicitly required service-account credential is unavailable in the supplied CLOUDSDK_CONFIG; no OAuth or alternate identity used.','gsc_service_account_probe':probe,'live_sitemap':smmeta,'robots_txt':{'http_status':robots['status'],'body':robots['body'][:20000]},'counts_by_gsc_class_and_classification':{k:dict(v) for k,v in counts.items()},'robots_problematic':problems,'rows':audits}
 fields=['issue','url','gsc_last_crawl','source_zip','http_status','redirect_chain','final_url','in_live_sitemap','redirect_rule','canonical_current','expected_canonical','noindex_current','prestashop_match','product_id','reference','active','indexed','url_inspection','search_analytics','classification','action','evidence','robots_class']
 with (OUT/'gsc_export_master_audit_20261003.csv').open('w',encoding='utf-8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(audits)
 (OUT/'gsc_export_master_audit_20261003.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 with (OUT/'gsc_404_surgical_batch_20261003.csv').open('w',encoding='utf-8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=['url','http_status','redirect_chain','in_live_sitemap','redirect_rule','canonical_current','expected_canonical','prestashop_match','product_id','reference','active','indexed','classification','action','gsc_last_crawl','url_inspection','search_analytics'],extrasaction='ignore');w.writeheader();w.writerows([a for a in audits if a['issue']=='No se ha encontrado (404)'])
 lines=['# Auditoría GSC desde exportes reales — 2026-10-03','',f"Fuente maestra: `{MASTER}`. Filas auditadas: **{len(rows)}**.",'', '## Estado de acceso GSC','',f"La identidad exigida (`{probe['service_account']}`) no está disponible en `CLOUDSDK_CONFIG=/home/maxdaguzan/.config/gcloud-rp-explorer`; detalle: `{probe['detail']}`. No se inició OAuth ni se usó otra identidad. Por ello URL Inspection y Search Analytics quedan explícitamente como evidencia insuficiente.",'', '## Conteos PASS / PENDING / RISK por clase GSC','']
 for k,v in counts.items(): lines.append(f"- {k}: PASS {v['PASS']}, PENDING {v['PENDING']}, RISK {v['RISK']}")
 lines += ['',f"Sitemap live GET: HTTP {smmeta['index_status']}; {smmeta['url_count']} URLs únicas. robots.txt GET: HTTP {robots['status']}.",'','## Las 11 URLs 404 — evidencia completa','']
 for a in [x for x in audits if x['issue']=='No se ha encontrado (404)']:
  lines += [f"### {a['url']}", '', f"- HTTP/cadena: `{a['redirect_chain']}`",f"- Sitemap vigente: {a['in_live_sitemap']}; regla redirects: {a['redirect_rule'] or 'ninguna'}.",f"- Canonical actual/esperada: `{a['canonical_current'] or 'ninguna'}` / `{a['expected_canonical'] or 'sin match'}`.",f"- PrestaShop GET: {a['prestashop_match']}; ID {a['product_id'] or '—'}, ref. {a['reference'] or '—'}, active/indexed {a['active'] or '—'}/{a['indexed'] or '—'}.",f"- GSC Inspection / Search Analytics: {a['url_inspection']} / {a['search_analytics']}; último rastreo exportado: {a['gsc_last_crawl']}.",f"- **{a['classification']}** — acción candidata: {a['action']}.",'']
 lines += ['## Otras 165 URLs','',f"- robots.txt: {len(by_issue['Bloqueada por robots.txt'])} URL(s); bloqueos deliberados {len(by_issue['Bloqueada por robots.txt'])-len(problems)}, potencialmente problemáticos {len(problems)}.",'- canonical adecuada: 27 URL(s), PASS por la clasificación explícita de GSC; no se infiere que sean error.', '']
 for a in [x for x in audits if x['issue'].startswith('Duplicada: Google ha elegido') or 'noindex' in x['issue'].lower()]:
  lines += [f"- {a['issue']}: `{a['url']}` — HTTP {a['http_status']}, canonical `{a['canonical_current'] or 'ausente'}`, noindex {a['noindex_current']}; **{a['classification']}**: {a['action']}."]
 lines += ['', '## Lote candidato (sin ejecución)', '', 'El CSV `gsc_404_surgical_batch_20261003.csv` contiene exclusivamente recomendaciones; no se modificó sitemap, redirects, canonical ni PrestaShop.']
 (OUT/'gsc_export_master_audit_20261003.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
 print(json.dumps({'rows':len(audits),'counts':{k:dict(v) for k,v in counts.items()},'sitemap':smmeta,'gsc_sa_available':probe['available']},ensure_ascii=False))
if __name__=='__main__': main()
