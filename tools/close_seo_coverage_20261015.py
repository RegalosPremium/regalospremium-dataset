#!/usr/bin/env python3
"""Backed-up, bounded PrestaShop category edits. Dry-run unless --apply."""
import argparse,csv,datetime,hashlib,html,json,os,time
from pathlib import Path
from xml.etree import ElementTree as ET
from urllib.request import Request,urlopen
from urllib.error import HTTPError
import base64
ROOT=Path(__file__).resolve().parents[1]
BASE='https://regalospremium.cl'
MARKER='rp-family-coverage-20261015'

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--apply',action='store_true');ap.add_argument('--env-file');ap.add_argument('--backup-dir',required=True);args=ap.parse_args()
    cfg=dict(os.environ)
    if args.env_file:
        for line in Path(args.env_file).read_text().splitlines():
            if '=' in line and not line.lstrip().startswith('#'):
                k,v=line.split('=',1);cfg.setdefault(k.strip(),v.strip().strip("'\""))
    key=cfg.get('PRESTASHOP_WS_KEY') or cfg.get('PRESTASHOP_API_KEY')
    if not key:raise SystemExit('PrestaShop key required')
    auth='Basic '+base64.b64encode((key+':').encode()).decode()
    def req(method,path,body=None):
        request=Request(BASE+'/webservice/dispatcher.php?url='+path,data=body,method=method,headers={'Authorization':auth,'Accept':'application/xml','Content-Type':'application/xml'})
        with urlopen(request,timeout=60) as r:return r.read()
    def get(cid):
        raw=req('GET',f'categories/{cid}');root=ET.fromstring(raw);return raw,root,root.find('category')
    def sanitize(c):
        for tag in ('level_depth','nb_products_recursive'):
            n=c.find(tag)
            if n is not None:c.remove(n)
    def desc(c):
        langs=c.findall('description/language');return next((n for n in langs if n.get('id')=='1'),langs[0])
    with (ROOT/'data/seo/seo_hub_family_links.csv').open(encoding='utf-8-sig') as f:links=list(csv.DictReader(f))
    # Explicit, observed dangling IDs only. Never remove an existing product.
    cleanup={}  # Category association writes are ignored by this Webservice; do not claim cleanup.
    # Fresh product ID existence guard before any write.
    raw=req('GET','products&display=[id]');existing={n.get('id') or n.findtext('id') for n in ET.fromstring(raw).findall('.//products/product')}
    if not existing:raise RuntimeError('empty product ID inventory')
    backup=Path(args.backup_dir)
    if args.apply:backup.mkdir(parents=True,exist_ok=False)
    records=[]
    for cid in (140,141):
        raw,root,c=get(cid);before_desc=desc(c).text or '';wanted=cleanup.get(cid,set())
        if wanted & existing:raise RuntimeError('cleanup ID now exists; refresh plan')
        before_ids={n.findtext('id') for n in c.findall('associations/products/product')}
        removed=[]
        for n in list(c.findall('associations/products/product')):
            if n.findtext('id') in wanted:
                removed.append(n.findtext('id'));c.find('associations/products').remove(n)
        expected_links=[]
        if cid in (140,141):
            owner=BASE+('/regalos-corporativos/' if cid==140 else '/regalos-publicitarios/')
            rows=[r for r in links if r['owner_url']==owner]
            if MARKER in before_desc:raise RuntimeError('coverage block already exists; inspect before rerunning')
            items=[]
            for r in rows:
                items.append('<li><a href="'+html.escape(r['landing_url'],quote=True)+'">'+html.escape(r['familia'])+'</a>: <a href="'+html.escape(r['product_url'],quote=True)+'">ver una opción para personalizar</a>.</li>')
                expected_links.append(r['product_url'])
            block='<section id="'+MARKER+'"><h2>Ideas por tipo de producto</h2><ul>'+''.join(items)+'</ul><h2>Campañas temáticas para promociones específicas</h2><p>Tenemos disponibles campañas temáticas para promociones específicas. Preparamos una selección de productos y personalización según el objetivo, público y ocasión: fin de año, Día de la Madre, verano, tecnología, actividades recreativas y acciones promocionales. Cotice su campaña por volumen con atención personalizada.</p></section>'
            desc(c).text=before_desc+'\n'+block
        sanitize(c);payload=ET.tostring(root,encoding='utf-8',xml_declaration=True)
        rec={'category_id':cid,'removed_dangling_ids':removed,'family_links':len(expected_links),'mode':'APPLY' if args.apply else 'DRY_RUN','before_sha256':hashlib.sha256(raw).hexdigest()}
        if args.apply:
            (backup/f'category_{cid}_before.xml').write_bytes(raw)
            try:
                req('PUT',f'categories/{cid}',payload);after_raw,_,after=get(cid)
                after_ids={n.findtext('id') for n in after.findall('associations/products/product')}
                text=desc(after).text or ''
                ok=after_ids==before_ids-wanted and not (after_ids & wanted) and all(u in text for u in expected_links) and before_desc in text
                if not ok:raise RuntimeError('category read-back mismatch')
                rec.update(status='PASS',after_sha256=hashlib.sha256(after_raw).hexdigest())
                (backup/f'category_{cid}_after.xml').write_bytes(after_raw)
            except Exception:
                original=ET.fromstring(raw);sanitize(original.find('category'));req('PUT',f'categories/{cid}',ET.tostring(original,encoding='utf-8',xml_declaration=True))
                raise
        records.append(rec);print(json.dumps(rec),flush=True);time.sleep(.5)
    report={'timestamp':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS' if args.apply else 'DRY_RUN','backup':str(backup),'categories':records}
    if args.apply:(ROOT/'reports/seo/coverage_apply_20261015.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()
