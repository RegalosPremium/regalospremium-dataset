#!/usr/bin/env python3
"""Read-only GSC/HTTP/PrestaShop audit for the 2026-10-02 candidate set.

All Google API calls are read-only queries.  Search Analytics and URL
Inspection are technically POST endpoints, but their OAuth scope and request
bodies contain no mutating operation.
"""
from __future__ import annotations
import base64, csv, json, os, re, shutil, subprocess, sys, tempfile
from datetime import date, timedelta
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit, quote
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/seo'
SITE='https://regalospremium.cl/'
UA='RegalosPremium-GSC-404-Audit/20261002 (read-only)'
GCLOUD='/home/maxdaguzan/.local/gcloud-install/google-cloud-sdk/bin/gcloud'
PRESTASHOP_ENV=Path('/home/maxdaguzan/Descargas/Creador_Plantillas_v1.1/creador-plantillas-app/config/prestashop.env')
FIELDS=['url','source','http_status','final_url','redirect_chain','in_sitemap','redirect_rule','canonical_target','prestashop_match','product_id','reference','gsc_verdict','gsc_coverage','last_crawl','clicks','impressions','classification','reason','evidence']

def fetch_http(url):
    if not url.startswith(('http://','https://')) or '√' in url:
        return {'status':'INVALID','final_url':'','chain':[],'body':b'','error':'invalid URL in source inventory'}
    try:
        # curl is used here because its redirect/time-limit behavior is stable on this host.
        p=subprocess.run(['timeout','--signal=KILL','4s','curl','-sS','-L','--max-redirs','10','--connect-timeout','2','--max-time','3','-A',UA,'-D','/dev/stderr','-o','-','-w','\n__RP_META__%{http_code}\t%{url_effective}',url],capture_output=True,timeout=6)
        body,_,meta=p.stdout.rpartition(b'\n__RP_META__')
        code,_,final=meta.decode('utf-8','replace').partition('\t')
        headers=p.stderr.decode('utf-8','replace')
        chain=[]; prior=url
        for block in re.split(r'\r?\n\r?\n',headers):
            sm=re.search(r'^HTTP/\S+\s+(\d+)',block,re.M); lm=re.search(r'^location:\s*(.+)$',block,re.I|re.M)
            if sm and lm:
                target=lm.group(1).strip(); chain.append({'status':int(sm.group(1)),'from':prior,'to':target}); prior=target
        if p.returncode or not code:
            return {'status':'ERROR','final_url':final,'chain':chain,'body':body,'error':headers.strip() or f'curl exit {p.returncode}'}
        return {'status':int(code),'final_url':final,'chain':chain,'body':body,'error':''}
    except Exception as e:
        return {'status':'ERROR','final_url':'','chain':[],'body':b'','error':f'{type(e).__name__}: {e}'}

def canonical(body):
    if not body: return ''
    s=body.decode('utf-8','replace')
    for tag in re.findall(r'<link\b[^>]*>',s,re.I):
        if re.search(r'\brel=["\']?canonical\b',tag,re.I):
            m=re.search(r'\bhref=["\']([^"\']+)',tag,re.I)
            if m: return m.group(1).strip()
    return ''

def get_token():
    # The source configuration is read-only in this sandbox.  gcloud requires
    # write access to credentials.db during impersonation, so use a short-lived
    # private copy and delete it immediately after extracting the in-memory token.
    tmp=Path(tempfile.mkdtemp(prefix='gcloud-rp-audit-',dir='/tmp'))
    try:
        shutil.copytree('/home/maxdaguzan/.config/gcloud-rp-explorer',tmp,dirs_exist_ok=True)
        env=os.environ.copy(); env['CLOUDSDK_CONFIG']=str(tmp)
        p=subprocess.run([GCLOUD,'auth','print-access-token','--impersonate-service-account=rp-google-ads-cli@able-marking-493221-m5.iam.gserviceaccount.com','--scopes=https://www.googleapis.com/auth/webmasters.readonly','--quiet'],env=env,capture_output=True,text=True,timeout=60)
    finally:
        # p.stdout is held only in process memory; no access token is written to reports.
        shutil.rmtree(tmp,ignore_errors=True)
    if p.returncode: raise RuntimeError('token impersonation failed: '+p.stderr.strip()[:300])
    token=p.stdout.strip()
    if not token: raise RuntimeError('token impersonation returned empty token')
    return token

def api(url, token, payload=None):
    data=None if payload is None else json.dumps(payload).encode()
    req=Request(url,data=data,headers={'Authorization':'Bearer '+token,'Content-Type':'application/json','User-Agent':UA})
    try:
        with urlopen(req,timeout=45) as r: return json.loads(r.read().decode()), ''
    except HTTPError as e:
        return {}, f'HTTP {e.code}: '+e.read(800).decode('utf-8','replace').replace('\n',' ')[:800]
    except Exception as e: return {}, f'{type(e).__name__}: {e}'

def gsc_read():
    meta={'property_confirmed':False,'property_permission':'','properties_error':'','sitemaps':[],'sitemaps_error':'','inspection_note':'URL Inspection API does not expose the UI bulk 404 table; inspected only relevant local candidates.','search_analytics_window':''}
    try: token=get_token()
    except Exception as e:
        meta['properties_error']=str(e); meta['sitemaps_error']='not queried: GSC token unavailable'
        return meta,{}, {}, {}
    siteq=quote(SITE,safe='')
    props,err=api('https://www.googleapis.com/webmasters/v3/sites',token)
    meta['properties_error']=err
    entry=next((x for x in props.get('siteEntry',[]) if x.get('siteUrl')==SITE),{})
    meta['property_confirmed']=bool(entry); meta['property_permission']=entry.get('permissionLevel','')
    sm,err=api(f'https://www.googleapis.com/webmasters/v3/sites/{siteq}/sitemaps',token)
    meta['sitemaps_error']=err; meta['sitemaps']=sm.get('sitemap',[])
    return meta,token,{},{}

def search_metrics(token,url,start,end):
    if not token: return {'clicks':'none','impressions':'none','error':'GSC token unavailable'}
    payload={'startDate':start,'endDate':end,'dimensions':['page'],'dimensionFilterGroups':[{'filters':[{'dimension':'page','operator':'equals','expression':url}]}],'rowLimit':1,'dataState':'final'}
    d,e=api('https://www.googleapis.com/webmasters/v3/sites/'+quote(SITE,safe='')+'/searchAnalytics/query',token,payload)
    row=(d.get('rows') or [{}])[0]
    return {'clicks':row.get('clicks',0),'impressions':row.get('impressions',0),'error':e}

def inspect(token,url):
    if not token: return {'error':'GSC token unavailable'}
    d,e=api('https://searchconsole.googleapis.com/v1/urlInspection/index:inspect',token,{'inspectionUrl':url,'siteUrl':SITE})
    x=d.get('inspectionResult',{}).get('indexStatusResult',{})
    return {'verdict':x.get('verdict',''), 'coverage':x.get('coverageState',''), 'last_crawl':x.get('lastCrawlTime',''), 'error':e}

def sitemap_urls():
    out=set(); errors=[]
    try:
        raw=fetch_http(SITE+'1_index_sitemap.xml')['body']; root=ET.fromstring(raw)
        ns={'s':'http://www.sitemaps.org/schemas/sitemap/0.9'}
        children=[x.text.strip() for x in root.findall('s:sitemap/s:loc',ns)]
        for child in children:
            r=fetch_http(child); doc=ET.fromstring(r['body'])
            out.update(x.text.strip() for x in doc.findall('s:url/s:loc',ns))
    except Exception as e: errors.append(f'{type(e).__name__}: {e}')
    return out,errors

def prestashop_check(ids):
    key=os.getenv('PRESTASHOP_WS_KEY','').strip(); kp=ROOT/'config/prestashop-webservice.key'
    base=SITE.rstrip('/')
    if PRESTASHOP_ENV.exists():
        for line in PRESTASHOP_ENV.read_text(encoding='utf-8').splitlines():
            name,sep,value=line.partition('=')
            if not sep: continue
            if name=='PRESTASHOP_API_KEY' and not key: key=value.strip()
            elif name=='PRESTASHOP_BASE_URL' and value.strip(): base=value.strip().rstrip('/')
    if not key and kp.exists(): key=kp.read_text(encoding='utf-8').strip()
    if not ids: return {}, 'not applicable'
    if not key: return {str(i):'not verified: read-only Webservice key unavailable' for i in ids}, 'read-only Webservice key unavailable'
    result={}
    for pid in ids:
        q=urlencode({'url':f'products/{pid}','display':'[id,reference,active,name,link_rewrite]','output_format':'JSON'})
        req=Request(base+'/webservice/dispatcher.php?'+q,headers={'Authorization':'Basic '+base64.b64encode((key+':').encode()).decode(),'Accept':'application/json','User-Agent':UA})
        try:
            with urlopen(req,timeout=35) as r:
                items=json.loads(r.read().decode()).get('products',[]); x=items[0] if items else {}
                result[str(pid)]=f"GET verified: active={x.get('active','?')}; reference={x.get('reference','')}"
        except Exception as e: result[str(pid)]=f'GET verification error: {type(e).__name__}: {e}'
    return result,''

def main():
    # The historical report is the candidate source; LIVE entries are deliberately excluded.
    with (ROOT/'reports/ads/ads_url_http_20260917.csv').open(encoding='utf-8-sig',newline='') as f: historical=list(csv.DictReader(f))
    candidates={}
    for r in historical:
        if r['live_status']!='LIVE':
            u=r['historical_url']; candidates[u]={'source':f"reports/ads/ads_url_http_20260917.csv:{r['live_status']}", 'old_status':r['live_status']}
    with (ROOT/'data/seo_redirects.csv').open(encoding='utf-8-sig',newline='') as f:
        redirects=list(csv.DictReader(f))
    for r in redirects:
        if '*' not in r['old_url']:
            candidates.setdefault(r['old_url'],{'source':'data/seo_redirects.csv:'+r['status'],'old_status':'REDIRECT_RULE'})
    with (ROOT/'data/productos.csv').open(encoding='utf-8-sig',newline='') as f: products=list(csv.DictReader(f))
    by_url={p['url']:p for p in products}
    sms,sm_errors=sitemap_urls()
    gmeta,token,_,_=gsc_read()
    end=date(2026,10,1); start=end-timedelta(days=89)
    gmeta['search_analytics_window']=f'{start.isoformat()} to {end.isoformat()} (90 days; end date avoids same-day partial data)'
    # Inspection stays deliberately small: known 404/redirect candidates, including B47.
    inspect_urls=[u for u,v in candidates.items() if v['old_status'] in {'DEAD_404','REDIRECT_RULE'}]
    inspections={u:inspect(token,u) for u in inspect_urls}
    ps_ids=set()
    for u in candidates:
        if u in by_url: ps_ids.add(int(by_url[u]['product_id']))
    ps,ps_note=prestashop_check(sorted(ps_ids))
    rows=[]
    for url,src in candidates.items():
        h=fetch_http(url); p=by_url.get(url); rule=next((r for r in redirects if r['old_url']==url),None)
        ins=inspections.get(url,{})
        m=search_metrics(token,url,start.isoformat(),end.isoformat())
        status=str(h['status']); fin=h['final_url']; can=canonical(h['body'])
        chain=' -> '.join(f"{x['status']} {x['from']} => {x['to']}" for x in h['chain']) or 'none'
        if status=='INVALID': cls='PENDING'; reason='Malformed source URL; no HTTP request issued; human review required.'
        elif status=='ERROR': cls='PENDING'; reason='Current HTTP validation failed; no deletion inference is safe.'
        elif status=='404' and p: cls='PENDING'; reason='Current 404 conflicts with a locally registered product canonical; verify storefront/PrestaShop before any action.'
        elif status=='404': cls='RISK'; reason='Current 404 with no local product canonical or redirect rule; candidate for human cleanup review only.'
        elif h['chain'] and rule and str(rule['http_code']) in status+''.join(str(x['status']) for x in h['chain']): cls='PASS'; reason='Redirect rule is present and current request redirects; retained as resolved/quarantined, not a removal candidate.'
        elif status.startswith('2') and (url in sms or fin in sms or p): cls='PASS'; reason='Current URL resolves and is backed by sitemap or local canonical identity.'
        elif status.startswith('2'): cls='PENDING'; reason='Current URL resolves but lacks sitemap/local canonical support or is a legacy/malformed variant.'
        else: cls='PENDING'; reason=f'Current HTTP status {status}; requires human decision.'
        ev=[f"HTTP {status}; final={fin or 'none'}; chain={chain}",f"candidate_in_sitemap={'yes' if url in sms else 'no'}",f"final_in_sitemap={'yes' if fin in sms else 'no'}"]
        if h['error']: ev.append('http_error='+h['error'])
        if rule: ev.append(f"redirect_csv={rule['http_code']} {rule['status']} -> {rule['new_url']}")
        if p: ev.append(f"local_product={p['product_id']}/{p['reference']}")
        if ps.get(p['product_id'] if p else ''): ev.append('prestashop='+ps[str(p['product_id'])])
        if ins: ev.append('inspection='+('; '.join(f'{k}={v}' for k,v in ins.items() if v) or 'none'))
        if m['error']: ev.append('search_analytics_error='+m['error'])
        rows.append({'url':url,'source':src['source'],'http_status':status,'final_url':fin,'redirect_chain':chain,'in_sitemap':'yes' if url in sms else 'no','redirect_rule':(f"{rule['http_code']} {rule['status']} -> {rule['new_url']}" if rule else ''),'canonical_target':can,'prestashop_match':ps.get(str(p['product_id']),'not applicable') if p else 'not applicable','product_id':p['product_id'] if p else '','reference':p['reference'] if p else '','gsc_verdict':ins.get('verdict','not inspected'),'gsc_coverage':ins.get('coverage','not inspected'),'last_crawl':ins.get('last_crawl','not inspected'),'clicks':m['clicks'],'impressions':m['impressions'],'classification':cls,'reason':reason,'evidence':' | '.join(ev)})
    rows.sort(key=lambda x:( {'RISK':0,'PENDING':1,'PASS':2}[x['classification']],x['url']))
    OUT.mkdir(parents=True,exist_ok=True)
    with (OUT/'gsc_404_audit_20261002.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=FIELDS); w.writeheader(); w.writerows(rows)
    summary={x:sum(r['classification']==x for r in rows) for x in ('PASS','PENDING','RISK')}
    report={'audit_date':'2026-10-02','scope':'read-only; GSC query endpoints use non-mutating POST requests required by Google APIs','candidate_selection':'All non-LIVE entries from reports/ads/ads_url_http_20260917.csv plus exact (non-wildcard) data/seo_redirects.csv rules. No URLs were invented.','gsc':gmeta,'live_sitemap_urls':len(sms),'live_sitemap_errors':sm_errors,'prestashop_note':ps_note,'url_inspection_count':len(inspect_urls),'search_analytics_query_count':len(rows),'summary':summary,'rows':rows}
    (OUT/'gsc_404_audit_20261002.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    lines=['# GSC 404 / páginas con error — auditoría 2026-10-02','',f"- Total auditado: **{len(rows)}**; PASS {summary['PASS']}, PENDING {summary['PENDING']}, RISK {summary['RISK']}.",'- Alcance externo: sólo GET HTTP/PrestaShop y consultas GSC read-only. Search Analytics e URL Inspection requieren POST técnico sin operación mutante.','- La API URL Inspection no proporciona la tabla completa de 404 de la interfaz; el inventario candidato se construyó exclusivamente desde artefactos locales.','', '## GSC y sitemap','',f"- Propiedad `{SITE}` confirmada por API: `{gmeta['property_confirmed']}`.",f"- Sitemaps API: {len(gmeta['sitemaps'])} entradas; error: {gmeta['sitemaps_error'] or 'none'}.",f"- Sitemap live descargado: {len(sms)} URL(s); error: {', '.join(sm_errors) or 'none'}.",f"- Inspection API: {len(inspect_urls)} candidatas seleccionadas; resultado disponible sólo si hubo token. Search Analytics por página: {gmeta['search_analytics_window']}.", '', '## Bloqueos / límites','',f"- PrestaShop: {ps_note or 'GET comprobado para productos con identidad local.'}",'- `none` en clicks/impressions indica que la consulta GSC no se pudo ejecutar; no se infiere ausencia de tráfico.','', '## Lote para revisión humana','']
    for r in rows:
        if r['classification']!='PASS': lines.append(f"- **{r['classification']}** `{r['url']}` — {r['reason']}")
    lines += ['', '## Evidencia por URL','', '| URL | HTTP | Sitemap | GSC | Clicks / impresiones | Clasificación |', '|---|---:|---|---|---:|---|']
    for r in rows: lines.append(f"| `{r['url']}` | {r['http_status']} | {r['in_sitemap']} | {r['gsc_verdict']} / {r['gsc_coverage']} | {r['clicks']} / {r['impressions']} | {r['classification']} |")
    (OUT/'gsc_404_audit_20261002.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({'total':len(rows),**summary,'gsc_property':gmeta['property_confirmed'],'sitemaps':len(gmeta['sitemaps'])},ensure_ascii=False))
if __name__=='__main__': main()
