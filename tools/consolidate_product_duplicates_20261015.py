#!/usr/bin/env python3
"""Consolidate four verified same-reference products with reversible 301 redirects."""
import argparse,base64,csv,datetime,hashlib,json,os,re,unicodedata
from pathlib import Path
from urllib.request import Request,urlopen
from xml.etree import ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
PAIRS={30:356,418:539,1396:1292,1430:1302}

def norm(s):return re.sub('[^a-z0-9]','',''.join(c for c in unicodedata.normalize('NFKD',s.lower()) if not unicodedata.combining(c)))
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--env-file',required=True);ap.add_argument('--backup-dir',required=True);ap.add_argument('--apply',action='store_true');a=ap.parse_args();cfg=dict(os.environ)
 for line in Path(a.env_file).read_text().splitlines():
  if '=' in line and not line.lstrip().startswith('#'):
   k,v=line.split('=',1);cfg.setdefault(k.strip(),v.strip().strip("'\""))
 key=cfg.get('PRESTASHOP_WS_KEY') or cfg.get('PRESTASHOP_API_KEY');assert key,'Missing key'
 auth='Basic '+base64.b64encode((key+':').encode()).decode()
 def request(method,pid,data=None):
  req=Request('https://regalospremium.cl/webservice/dispatcher.php?url=products/'+str(pid),data=data,method=method,headers={'Authorization':auth,'Content-Type':'application/xml','Accept':'application/xml'})
  with urlopen(req,timeout=60) as r:return r.read()
 def text(p,key):
  n=p.find(key);return (n.findtext('language') if n is not None and n.find('language') is not None else p.findtext(key)) or ''
 def sanitize(p):
  for tag in ('manufacturer_name','quantity'):
   n=p.find(tag)
   if n is not None:p.remove(n)
 backup=Path(a.backup_dir)
 if a.apply:backup.mkdir(parents=True,exist_ok=False)
 plans=[]
 for source,target in PAIRS.items():
  raw=request('GET',source);root=ET.fromstring(raw);p=root.find('product');t=ET.fromstring(request('GET',target)).find('product')
  assert text(t,'active')=='1','Target inactive'
  assert norm(text(p,'reference'))==norm(text(t,'reference')),'Reference differs'
  assert norm(text(p,'name'))==norm(text(t,'name')),'Name differs'
  assert not p.findall('associations/combinations/combination') and not t.findall('associations/combinations/combination'),'Variant requires separate review'
  for field,value in [('active','0'),('indexed','0'),('redirect_type','301-product'),('id_type_redirected',str(target))]:
   n=p.find(field)
   if n is None:n=ET.SubElement(p,field)
   n.text=value
  sanitize(p)
  rec={'source_product_id':source,'target_product_id':target,'reference':text(p,'reference'),'before_sha256':hashlib.sha256(raw).hexdigest(),'status':'DRY_RUN'}
  if a.apply:
   (backup/f'product_{source}_before.xml').write_bytes(raw)
   try:
    request('PUT',source,ET.tostring(root,encoding='utf-8',xml_declaration=True));after=request('GET',source);q=ET.fromstring(after).find('product')
    assert text(q,'active')=='0' and text(q,'redirect_type')=='301-product' and text(q,'id_type_redirected')==str(target),'Read-back mismatch'
    rec.update(status='PASS',after_sha256=hashlib.sha256(after).hexdigest());(backup/f'product_{source}_after.xml').write_bytes(after)
   except Exception:
    original=ET.fromstring(raw);sanitize(original.find('product'));request('PUT',source,ET.tostring(original,encoding='utf-8',xml_declaration=True));raise
  plans.append(rec);print(json.dumps(rec),flush=True)
 report={'timestamp':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS' if a.apply else 'DRY_RUN','backup':str(backup),'checks':plans,'basis':'Same normalized reference/name, dimensions and materials reviewed via Webservice; no combinations. Deactivated copies kept with built-in 301-product redirect; no deletion.'}
 if a.apply:(ROOT/'reports/seo/product_consolidation_20261015.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()
