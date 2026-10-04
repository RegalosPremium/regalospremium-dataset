#!/usr/bin/env python3
import os, datetime, json, xml.etree.ElementTree as ET
from pathlib import Path
import requests

ENV=Path("/home/maxdaguzan/Descargas/Creador_Plantillas_v1.1/creador-plantillas-app/config/prestashop.env")
for line in ENV.read_text().splitlines():
    if "=" in line and not line.lstrip().startswith("#"):
        k,v=line.split("=",1); os.environ.setdefault(k.strip(),v.strip().strip("'\""))
BASE=os.environ.get("PRESTASHOP_BASE_URL","https://regalospremium.cl").rstrip("/")
KEY=os.environ.get("PRESTASHOP_WS_KEY") or os.environ.get("PRESTASHOP_API_KEY")
API=BASE+"/webservice/dispatcher.php"
AUTH=(KEY,"")
BACK=Path("/home/maxdaguzan/RegalosPremium_Backups/seo_hubs_20261004/products")
BACK.mkdir(parents=True,exist_ok=True)
REPORT=Path("/home/maxdaguzan/regalospremium-dataset/reports/seo/seo_hub_product_associations_20261004.json")

MAP={
 140:[1481,1490,1467,1459,1431,1398,1486,1213,1491,1483,1469,1212],
 141:[1292,1377,1483,1431,1476,1300,1400,1329,558,1457,1287,1491],
}

def req(method,path,**kw):
    r=requests.request(method,API,params={"url":path},auth=AUTH,timeout=60,**kw)
    r.raise_for_status()
    return r

def sanitize(product):
    for tag in ("manufacturer_name","quantity"):
        n=product.find(tag)
        if n is not None:
            product.remove(n)

def get_product(pid):
    r=req("GET",f"products/{pid}",headers={"Accept":"application/xml"})
    root=ET.fromstring(r.content)
    return root,root.find("product"),r.content

def cats(product):
    a=product.find("associations")
    cs=a.find("categories") if a is not None else None
    return set(x.findtext("id","") for x in cs.findall("category")) if cs is not None else set()

def add_cat(product,cid):
    a=product.find("associations")
    if a is None: raise RuntimeError("associations absent")
    cs=a.find("categories")
    if cs is None: raise RuntimeError("categories association absent")
    if str(cid) not in cats(product):
        n=ET.SubElement(cs,"category"); ET.SubElement(n,"id").text=str(cid)

results=[]
for cid,pids in MAP.items():
    for pid in pids:
        root,p,orig=get_product(pid)
        before={"default":p.findtext("id_category_default",""),"active":p.findtext("active",""),"indexed":p.findtext("indexed",""),"cats":sorted(cats(p))}
        bfile=BACK/f"product_{pid}_before_hub_{cid}.xml"
        if not bfile.exists(): bfile.write_bytes(orig)
        add_cat(p,cid); sanitize(p)
        payload=ET.tostring(root,encoding="utf-8",xml_declaration=True)
        try:
            req("PUT",f"products/{pid}",data=payload,headers={"Content-Type":"application/xml","Accept":"application/xml"})
            _,p2,_=get_product(pid)
            after={"default":p2.findtext("id_category_default",""),"active":p2.findtext("active",""),"indexed":p2.findtext("indexed",""),"cats":sorted(cats(p2))}
            ok=(str(cid) in after["cats"] and before["default"]==after["default"] and before["active"]==after["active"] and before["indexed"]==after["indexed"])
            if not ok:
                req("PUT",f"products/{pid}",data=bfile.read_bytes(),headers={"Content-Type":"application/xml","Accept":"application/xml"})
                status="ROLLBACK"
            else:
                status="PASS"
            results.append({"hub_category":cid,"product_id":pid,"status":status,"before":before,"after":after,"backup":str(bfile)})
            print(cid,pid,status)
        except Exception as e:
            try:
                req("PUT",f"products/{pid}",data=bfile.read_bytes(),headers={"Content-Type":"application/xml","Accept":"application/xml"})
                rb="rollback_sent"
            except Exception as re:
                rb=f"rollback_failed:{type(re).__name__}"
            results.append({"hub_category":cid,"product_id":pid,"status":"ERROR","error":f"{type(e).__name__}:{e}","rollback":rb,"backup":str(bfile)})
            print(cid,pid,"ERROR",type(e).__name__)
            break

REPORT.write_text(json.dumps({"timestamp":datetime.datetime.now(datetime.timezone.utc).isoformat(),"results":results},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("REPORT",REPORT)
