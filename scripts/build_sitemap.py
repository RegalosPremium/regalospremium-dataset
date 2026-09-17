#!/usr/bin/env python3
from pathlib import Path
import csv
from xml.etree.ElementTree import Element, SubElement, ElementTree, register_namespace
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"dist/sitemap-products.xml"
with (ROOT/"data/productos.csv").open(encoding="utf-8-sig",newline="") as f:
    urls=sorted({r["url"] for r in csv.DictReader(f) if r["url"]})
ns="http://www.sitemaps.org/schemas/sitemap/0.9"
register_namespace("",ns)
root=Element(f"{{{ns}}}urlset")
for url in urls:
    node=SubElement(root,f"{{{ns}}}url")
    SubElement(node,f"{{{ns}}}loc").text=url
OUT.parent.mkdir(exist_ok=True)
ElementTree(root).write(OUT,encoding="utf-8",xml_declaration=True)
print(f"wrote {OUT} with {len(urls)} unique URLs")
