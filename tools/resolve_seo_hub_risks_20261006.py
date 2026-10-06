#!/usr/bin/env python3
import os,json,datetime,time,xml.etree.ElementTree as ET
from pathlib import Path
import requests

ROOT=Path(__file__).resolve().parents[1]
ENV=Path('/home/maxdaguzan/Descargas/Creador_Plantillas_v1.1/creador-plantillas-app/config/prestashop.env')
for line in ENV.read_text().splitlines():
    if '=' in line and not line.lstrip().startswith('#'):
        k,v=line.split('=',1);os.environ.setdefault(k.strip(),v.strip().strip("'\""))
BASE=os.environ.get('PRESTASHOP_BASE_URL','https://regalospremium.cl').rstrip('/')
KEY=os.environ.get('PRESTASHOP_WS_KEY') or os.environ.get('PRESTASHOP_API_KEY')
assert KEY,'Missing PrestaShop key'
API=BASE+'/webservice/dispatcher.php';AUTH=(KEY,'')
STAMP=datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
BACK=Path('/home/maxdaguzan/RegalosPremium_Backups')/f'seo_riskfix_{STAMP}'
BACK.mkdir(parents=True,exist_ok=False)
REPORT=ROOT/'reports/seo/seo_riskfix_20261006.json'

CHANGES={
1431:{'add':{141},'remove':{140}},
1483:{'add':{140},'remove':{141}},
1491:{'add':{140},'remove':{141}},
1502:{'add':{140},'remove':{141}},
1487:{'add':{141},'remove':{140}},
1495:{'add':{141},'remove':{140}},
1186:{'slug':'mug-metalico-bambu-aurus-m56'},
1187:{'slug':'botella-pet-tapa-acero-vivid-m44'},
1251:{'slug':'parlante-cana-trigo-life-b98'},
}
URLS={
1186:BASE+'/mugs-ecologicos-publicitarios/mug-metalico-bambu-aurus-m56.html',
1187:BASE+'/botellas-plasticas-publicitarias/botella-pet-tapa-acero-vivid-m44.html',
1251:BASE+'/audio-publicitario/parlante-cana-trigo-life-b98.html',
}

def req(method,path,**kw):
    r=requests.request(method,API,params={'url':path},auth=AUTH,timeout=60,**kw)
    r.raise_for_status();return r

def get(pid):
    r=req('GET',f'products/{pid}',headers={'Accept':'application/xml'})
    root=ET.fromstring(r.content);return root,root.find('product'),r.content

def sanitize(p):
    for tag in ('manufacturer_name','quantity'):
        n=p.find(tag)
        if n is not None:p.remove(n)

def cats(p):
    a=p.find('associations');cs=a.find('categories') if a is not None else None
    return set(x.findtext('id','') for x in cs.findall('category')) if cs is not None else set()

def update_cats(p,add,remove):
    a=p.find('associations');cs=a.find('categories') if a is not None else None
    if cs is None:raise RuntimeError('categories association absent')
    for node in list(cs.findall('category')):
        if node.findtext('id','') in {str(x) for x in remove}:cs.remove(node)
    have=cats(p)
    for cid in add:
        if str(cid) not in have:
            n=ET.SubElement(cs,'category');ET.SubElement(n,'id').text=str(cid)

def update_slug(p,slug):
    n=p.find('link_rewrite')
    if n is None:raise RuntimeError('link_rewrite absent')
    langs=n.findall('language')
    if not langs:raise RuntimeError('link_rewrite language absent')
    target=next((x for x in langs if x.get('id')=='1'),langs[0]);target.text=slug

original={};before={};applied=[]
try:
    for pid in CHANGES:
        root,p,raw=get(pid);original[pid]=raw
        (BACK/f'product_{pid}_before.xml').write_bytes(raw)
        before[pid]={'categories':sorted(cats(p),key=int),'slug':p.find('link_rewrite/language').text}
        ch=CHANGES[pid]
        update_cats(p,ch.get('add',set()),ch.get('remove',set()))
        if ch.get('slug'):update_slug(p,ch['slug'])
        sanitize(p)
        req('PUT',f'products/{pid}',data=ET.tostring(root,encoding='utf-8',xml_declaration=True),headers={'Content-Type':'application/xml','Accept':'application/xml'})
        applied.append(pid)

    results=[]
    for pid,ch in CHANGES.items():
        _,p,_=get(pid);actual_cats=cats(p);actual_slug=p.find('link_rewrite/language').text
        ok=all(str(x) in actual_cats for x in ch.get('add',set())) and all(str(x) not in actual_cats for x in ch.get('remove',set()))
        if ch.get('slug'):ok=ok and actual_slug==ch['slug']
        results.append({'product_id':pid,'status':'PASS' if ok else 'FAIL','before':before[pid],'after':{'categories':sorted(actual_cats,key=int),'slug':actual_slug}})
        if not ok:raise RuntimeError(f'verification failed for {pid}')

    http=[]
    for pid,url in URLS.items():
        r=requests.get(url,timeout=30,headers={'User-Agent':'Mozilla/5.0','Cache-Control':'no-cache'})
        from bs4 import BeautifulSoup
        s=BeautifulSoup(r.text,'html.parser');can=s.find('link',rel='canonical');canonical=can.get('href') if can else ''
        ok=r.status_code==200 and r.url==url and canonical==url
        http.append({'product_id':pid,'url':url,'http':r.status_code,'final_url':r.url,'canonical':canonical,'status':'PASS' if ok else 'FAIL'})
        if not ok:raise RuntimeError(f'HTTP/canonical verification failed for {pid}')

    payload={'timestamp':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS','backup':str(BACK),'changes':results,'http':http}
    REPORT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':'PASS','backup':str(BACK),'products':len(results),'http':http},ensure_ascii=False))
except Exception as e:
    rollback=[]
    for pid in reversed(applied):
        try:
            root=ET.fromstring(original[pid]);p=root.find('product');sanitize(p)
            req('PUT',f'products/{pid}',data=ET.tostring(root,encoding='utf-8',xml_declaration=True),headers={'Content-Type':'application/xml','Accept':'application/xml'})
            rollback.append({'product_id':pid,'status':'PASS'})
        except Exception as re:
            rollback.append({'product_id':pid,'status':'FAIL','error':f'{type(re).__name__}:{re}'})
    payload={'timestamp':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'ROLLBACK','error':f'{type(e).__name__}:{e}','backup':str(BACK),'rollback':rollback}
    REPORT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(payload,ensure_ascii=False));raise
