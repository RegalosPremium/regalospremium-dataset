#!/usr/bin/env python3
"""Validate the distributed product sitemap against the complete catalog."""
import csv,json,sys
from pathlib import Path
from xml.etree import ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]

def compare(catalog,xml):
    urls=[p['url'] for p in catalog]
    locs=[n.text or '' for n in ET.fromstring(xml).findall('{http://www.sitemaps.org/schemas/sitemap/0.9}url/{http://www.sitemaps.org/schemas/sitemap/0.9}loc')]
    missing=sorted(set(urls)-set(locs));extra=sorted(set(locs)-set(urls))
    return {'status':'PASS' if not missing and not extra and len(urls)==len(set(urls)) and len(locs)==len(set(locs)) else 'RISK','scope':'distributed sitemap/catalog equality; not HTTP or Google indexation','catalog_products':len(urls),'sitemap_urls':len(locs),'catalog_duplicates':len(urls)-len(set(urls)),'sitemap_duplicates':len(locs)-len(set(locs)),'missing':missing,'extra':extra}
if __name__=='__main__':
    with (ROOT/'data/productos.csv').open(encoding='utf-8-sig',newline='') as f:products=list(csv.DictReader(f))
    report=compare(products,(ROOT/'dist/sitemap-products.xml').read_bytes());print(json.dumps(report,ensure_ascii=False,indent=2));sys.exit(report['status']!='PASS')
