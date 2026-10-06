#!/usr/bin/env python3
import os, requests, xml.etree.ElementTree as ET, json, html
from pathlib import Path
from datetime import datetime, timezone

ENV=Path("/home/maxdaguzan/Descargas/Creador_Plantillas_v1.1/creador-plantillas-app/config/prestashop.env")
for line in ENV.read_text().splitlines():
    if "=" in line and not line.lstrip().startswith("#"):
        k,v=line.split("=",1); os.environ.setdefault(k.strip(),v.strip().strip("'\""))
BASE=os.environ.get("PRESTASHOP_BASE_URL","https://regalospremium.cl").rstrip("/")
KEY=os.environ.get("PRESTASHOP_WS_KEY") or os.environ.get("PRESTASHOP_API_KEY")
API=BASE+"/webservice/dispatcher.php"
assert KEY, "Missing PrestaShop key"
AUTH=(KEY,"")

HUBS=[
 {
  "slug":"regalos-corporativos",
  "name":"Regalos corporativos para empresas",
  "meta_title":"Regalos Corporativos para Empresas en Chile",
  "meta_description":"Regalos corporativos personalizados para empresas en Chile. Opciones premium, pedidos por volumen y cotización B2B con su logo.",
  "description":"""<p>En <strong>Regalos Premium</strong> reunimos regalos corporativos para empresas que buscan reconocer, fidelizar y fortalecer su identidad de marca. Esta selección B2B incluye alternativas para clientes, colaboradores, campañas internas, eventos y acciones de relacionamiento.</p>
<p>Trabajamos <strong>regalos para empresas</strong> personalizados con logo y pedidos por volumen, desde opciones de uso diario hasta <strong>regalos corporativos premium</strong>. Cotizamos cada proyecto según producto, cantidad y técnica de marcaje, con atención local y despacho en Chile.</p>
<p>Explore también <a href="/cuadernos-libretas-memo-set-publicitarios/">cuadernos y libretas corporativas</a>, <a href="/carpetas-y-portafolios-publicitarios/">carpetas y portafolios</a>, <a href="/power-bank-y-accesorios/">power banks y accesorios</a>, <a href="/regalos-corporativos-bambu/">regalos corporativos de bambú</a> y <a href="/boligrafos-metalicos-y-ejecutivos-publicitarios/">bolígrafos ejecutivos</a>.</p>""",
  "products":[1481,1490,1467,1459,1398,1486,1213,1491,1483,1469,1212,1502]
 },
 {
  "slug":"regalos-publicitarios",
  "name":"Regalos publicitarios personalizados",
  "meta_title":"Regalos Publicitarios y Merchandising Corporativo",
  "meta_description":"Regalos publicitarios y merchandising corporativo personalizados con logo para empresas en Chile. Cotización B2B y pedidos por volumen.",
  "description":"""<p>Los <strong>regalos publicitarios</strong> permiten mantener una marca presente en clientes, equipos y eventos mediante productos útiles y personalizables. Esta selección reúne artículos promocionales para campañas de marketing, ferias, activaciones y acciones corporativas.</p>
<p>Desarrollamos <strong>merchandising corporativo</strong> con logo para empresas y <strong>regalos publicitarios por mayor</strong>, cotizados según cantidad, producto y técnica de marcaje. Atendemos proyectos B2B en Chile sin publicar precios unitarios, porque cada requerimiento se evalúa de acuerdo con su volumen y personalización.</p>
<p>Revise categorías como <a href="/mugs-metalicos-publicitarios/">mugs metálicos</a>, <a href="/coolers-publicitarios/">coolers</a>, <a href="/boligrafos-y-lapices-publicitarios/">bolígrafos y lápices</a>, <a href="/lanyards-e-identificacion-empresa/">lanyards e identificación</a>, <a href="/bolsas-publicitarias-con-logotipo/">bolsas publicitarias</a> y <a href="/regalos-promocionales-tecnologicos/">tecnología promocional</a>.</p>""",
  "products":[1292,1377,1431,1476,1300,1400,1329,558,1457,1287,1487,1495]
 }
]

def get_by_slug(slug):
    r=requests.get(API,params={"url":"categories","display":"[id,id_parent,active,name,link_rewrite,meta_title,meta_description]","filter[link_rewrite]":f"[{slug}]","output_format":"JSON"},auth=AUTH,timeout=20)
    r.raise_for_status()
    data=r.json()
    if isinstance(data,list): return data
    return data.get("categories",[]) if isinstance(data,dict) else []

def lang(parent, tag, text):
    node=ET.SubElement(parent,tag)
    l=ET.SubElement(node,"language",{"id":"1"})
    l.text=text
    return node

def create(h):
    root=ET.Element("prestashop")
    c=ET.SubElement(root,"category")
    ET.SubElement(c,"id_parent").text="2"
    ET.SubElement(c,"active").text="1"
    ET.SubElement(c,"id_shop_default").text="1"
    ET.SubElement(c,"is_root_category").text="0"
    lang(c,"name",h["name"])
    lang(c,"link_rewrite",h["slug"])
    lang(c,"description",h["description"])
    lang(c,"meta_title",h["meta_title"])
    lang(c,"meta_description",h["meta_description"])
    lang(c,"meta_keywords","")
    assoc=ET.SubElement(c,"associations")
    products=ET.SubElement(assoc,"products")
    for pid in h["products"]:
        p=ET.SubElement(products,"product")
        ET.SubElement(p,"id").text=str(pid)
    body=ET.tostring(root,encoding="utf-8",xml_declaration=True)
    r=requests.post(API,params={"url":"categories"},data=body,auth=AUTH,timeout=30,headers={"Content-Type":"application/xml","Accept":"application/xml"})
    print("POST",h["slug"],r.status_code)
    if r.status_code not in (200,201):
        print(r.text[:2000])
        r.raise_for_status()
    try:
        rr=ET.fromstring(r.content)
        idnode=rr.find(".//category/id")
        return int(idnode.text) if idnode is not None and idnode.text else None
    except Exception:
        return None

result={"timestamp":datetime.now(timezone.utc).isoformat(),"created":[],"existing":[]}
for h in HUBS:
    existing=get_by_slug(h["slug"])
    if existing:
        print("EXISTS",h["slug"],existing)
        result["existing"].append({"slug":h["slug"],"records":existing})
        continue
    cid=create(h)
    after=get_by_slug(h["slug"])
    print("AFTER",h["slug"],after)
    result["created"].append({"slug":h["slug"],"id":cid,"records":after,"products":h["products"]})

out=Path("/home/maxdaguzan/regalospremium-dataset/reports/seo/seo_hubs_create_20261004.json")
out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("REPORT",out)
