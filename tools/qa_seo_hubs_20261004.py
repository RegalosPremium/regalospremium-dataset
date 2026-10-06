#!/usr/bin/env python3
import os,csv,json,re,requests
from pathlib import Path
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[1]
ENV=Path('/home/maxdaguzan/Descargas/Creador_Plantillas_v1.1/creador-plantillas-app/config/prestashop.env')
for line in ENV.read_text().splitlines():
    if '=' in line and not line.lstrip().startswith('#'):
        k,v=line.split('=',1);os.environ.setdefault(k.strip(),v.strip().strip("'\""))
BASE='https://regalospremium.cl'
KEY=os.environ.get('PRESTASHOP_WS_KEY') or os.environ.get('PRESTASHOP_API_KEY')
API=BASE+'/webservice/dispatcher.php'
AUTH=(KEY,'')

with (ROOT/'data/seo/seo_hub_product_selection.csv').open(encoding='utf-8-sig',newline='') as f:
    selection=list(csv.DictReader(f))
expected={}
for row in selection:
    expected.setdefault(int(row['hub_category']),set()).add(row['product_id'])

hubs=[
 {'id':140,'url':BASE+'/regalos-corporativos/','h1':'Regalos corporativos para empresas','terms':['regalos corporativos','regalos para empresas','regalos corporativos premium']},
 {'id':141,'url':BASE+'/regalos-publicitarios/','h1':'Regalos publicitarios personalizados','terms':['regalos publicitarios','merchandising corporativo','regalos publicitarios por mayor']},
]
sitemap=requests.get(BASE+'/1_es_0_sitemap.xml',timeout=25).text
out=[]
actual_sets={}
for h in hubs:
    r=requests.get(h['url'],timeout=25,headers={'User-Agent':'Mozilla/5.0','Cache-Control':'no-cache'})
    s=BeautifulSoup(r.text,'html.parser')
    can=s.find('link',rel='canonical');h1=s.find('h1');desc=s.find('meta',attrs={'name':'description'})
    api=requests.get(API,params={'url':f"categories/{h['id']}",'output_format':'JSON'},auth=AUTH,timeout=20).json()['category']
    products=api.get('associations',{}).get('products',[])
    ids={str(x['id']) for x in products};actual_sets[h['id']]=ids
    text=' '.join(s.stripped_strings).lower()
    rec={
      'id':h['id'],'url':h['url'],'http':r.status_code,'final_url':r.url,
      'canonical':can.get('href') if can else '','h1':h1.get_text(' ',strip=True) if h1 else '',
      'title':s.title.get_text(' ',strip=True) if s.title else '',
      'meta_description':desc.get('content') if desc else '',
      'noindex':bool(s.find('meta',attrs={'name':'robots','content':re.compile('noindex',re.I)})),
      'api_product_associations':len(ids),'api_product_ids':sorted(ids,key=int),
      'expected_product_ids':sorted(expected[h['id']],key=int),
      'exact_product_selection':ids==expected[h['id']],
      'in_sitemap':sitemap.count(h['url']),
      'terms_present':{t:t in text for t in h['terms']},
    }
    rec['pass']=all([
      rec['http']==200,rec['final_url']==h['url'],rec['canonical']==h['url'],
      rec['h1']==h['h1'],not rec['noindex'],rec['exact_product_selection'],
      rec['in_sitemap']==1,all(rec['terms_present'].values())
    ])
    out.append(rec)
overlap=sorted(actual_sets[140]&actual_sets[141],key=int)
status='PASS' if all(x['pass'] for x in out) and not overlap else 'FAIL'
path=ROOT/'reports/seo/seo_hubs_qa_20261006.json'
path.write_text(json.dumps({'status':status,'product_overlap':overlap,'hubs':out},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':status,'product_overlap':overlap,'hubs':[{'id':x['id'],'pass':x['pass'],'http':x['http'],'products':x['api_product_associations'],'exact':x['exact_product_selection'],'sitemap':x['in_sitemap']} for x in out]},ensure_ascii=False))
