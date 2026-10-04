#!/usr/bin/env python3
import os,json,datetime,xml.etree.ElementTree as ET
from pathlib import Path
import requests
ENV=Path("/home/maxdaguzan/Descargas/Creador_Plantillas_v1.1/creador-plantillas-app/config/prestashop.env")
for line in ENV.read_text().splitlines():
    if "=" in line and not line.lstrip().startswith("#"):
        k,v=line.split("=",1); os.environ.setdefault(k.strip(),v.strip().strip("'\""))
BASE=os.environ.get("PRESTASHOP_BASE_URL","https://regalospremium.cl").rstrip("/")
KEY=os.environ.get("PRESTASHOP_WS_KEY") or os.environ.get("PRESTASHOP_API_KEY")
API=BASE+"/webservice/dispatcher.php"; AUTH=(KEY,"")
BACK=Path("/home/maxdaguzan/RegalosPremium_Backups/seo_hubs_20261004/internal_links")
BACK.mkdir(parents=True,exist_ok=True)
REPORT=Path("/home/maxdaguzan/regalospremium-dataset/reports/seo/seo_hub_internal_links_20261004.json")
TARGETS={
44:('regalos-corporativos','Explore también nuestra selección de <a href="/regalos-corporativos/">regalos corporativos para empresas</a>, pensada para proyectos B2B, onboarding y reconocimiento.'),
43:('regalos-corporativos','Conozca además nuestros <a href="/regalos-corporativos/">regalos corporativos para empresas</a> para clientes, colaboradores y acciones ejecutivas.'),
34:('regalos-corporativos','Para programas de tecnología y trabajo híbrido, revise también nuestros <a href="/regalos-corporativos/">regalos corporativos para empresas</a>.'),
122:('regalos-publicitarios','Integre estos productos en campañas de <a href="/regalos-publicitarios/">regalos publicitarios y merchandising corporativo</a> personalizados.'),
62:('regalos-publicitarios','Vea también nuestra selección de <a href="/regalos-publicitarios/">regalos publicitarios y merchandising corporativo</a> para campañas y eventos.'),
114:('regalos-publicitarios','Combine estos artículos con otros <a href="/regalos-publicitarios/">regalos publicitarios personalizados</a> para campañas de marca y eventos.'),
74:('regalos-publicitarios','Complete su campaña con <a href="/regalos-publicitarios/">merchandising corporativo y regalos publicitarios</a> personalizados.'),
15:('regalos-publicitarios','Encuentre más opciones de <a href="/regalos-publicitarios/">regalos publicitarios y merchandising corporativo</a> para empresas.')
}
def req(m,path,**kw):
    r=requests.request(m,API,params={"url":path},auth=AUTH,timeout=60,**kw); r.raise_for_status(); return r
def get(cid):
    r=req("GET",f"categories/{cid}",headers={"Accept":"application/xml"}); root=ET.fromstring(r.content); return root,root.find("category"),r.content
def descnode(c):
    n=c.find("description"); l=n.find("language") if n is not None else None
    if l is None: raise RuntimeError("description language absent")
    return l
def sanitize(c):
    for tag in ("level_depth","nb_products_recursive"):
        n=c.find(tag)
        if n is not None: c.remove(n)
results=[]
for cid,(slug,sentence) in TARGETS.items():
    root,c,orig=get(cid); d=descnode(c); before=d.text or ""
    backup=BACK/f"category_{cid}_before.xml"
    if not backup.exists(): backup.write_bytes(orig)
    if f'href="/{slug}/"' in before:
        results.append({"category_id":cid,"status":"SKIP_ALREADY_PRESENT","target":slug,"backup":str(backup)}); print(cid,"SKIP"); continue
    d.text=before+("\n" if before.strip() else "")+f"<p>{sentence}</p>"; sanitize(c)
    payload=ET.tostring(root,encoding="utf-8",xml_declaration=True)
    try:
        req("PUT",f"categories/{cid}",data=payload,headers={"Content-Type":"application/xml","Accept":"application/xml"})
        _,c2,_=get(cid); after=descnode(c2).text or ""
        ok=f'href="/{slug}/"' in after and before in after
        if not ok:
            br=ET.fromstring(backup.read_bytes()); bc=br.find("category"); sanitize(bc); req("PUT",f"categories/{cid}",data=ET.tostring(br,encoding="utf-8",xml_declaration=True),headers={"Content-Type":"application/xml","Accept":"application/xml"}); status="ROLLBACK"
        else: status="PASS"
    except Exception as e:
        try: br=ET.fromstring(backup.read_bytes()); bc=br.find("category"); sanitize(bc); req("PUT",f"categories/{cid}",data=ET.tostring(br,encoding="utf-8",xml_declaration=True),headers={"Content-Type":"application/xml","Accept":"application/xml"})
        except Exception: pass
        status="ERROR"
        results.append({"category_id":cid,"status":status,"target":slug,"error":f"{type(e).__name__}:{e}","backup":str(backup)}); print(cid,status); continue
    results.append({"category_id":cid,"status":status,"target":slug,"backup":str(backup)}); print(cid,status)
REPORT.write_text(json.dumps({"timestamp":datetime.datetime.now(datetime.timezone.utc).isoformat(),"results":results},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("REPORT",REPORT)
