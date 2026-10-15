#!/usr/bin/env python3
from pathlib import Path
import csv
from xml.etree.ElementTree import Element, SubElement, ElementTree, register_namespace
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"dist/sitemap-products.xml"
with (ROOT/"data/productos.csv").open(encoding="utf-8-sig",newline="") as f:
    products=list(csv.DictReader(f))
    values=[r["url"] for r in products]
    if any(not u for u in values) or len(values)!=len(set(values)):
        raise SystemExit("Catalog contains empty or duplicate URLs; refusing sitemap build")
    urls=set(values)
exclude=set()
redirects=ROOT/"data/seo_redirects.csv"
if redirects.exists():
    with redirects.open(encoding="utf-8-sig",newline="") as f:
        for r in csv.DictReader(f):
            if r.get("status")=="QUARANTINE" and "*" not in r.get("old_url",""):
                exclude.add(r["old_url"])
if urls & exclude:
    raise SystemExit("Active catalog URL is quarantined; resolve it before building")
urls=sorted(urls)
ns="http://www.sitemaps.org/schemas/sitemap/0.9"
register_namespace("",ns)
root=Element(f"{{{ns}}}urlset")
for url in urls:
    node=SubElement(root,f"{{{ns}}}url")
    SubElement(node,f"{{{ns}}}loc").text=url
OUT.parent.mkdir(exist_ok=True)
ElementTree(root).write(OUT,encoding="utf-8",xml_declaration=True)
print(f"wrote {OUT} with {len(urls)} unique URLs")
