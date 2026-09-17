#!/usr/bin/env python3
from pathlib import Path
import csv, json, collections, sys
ROOT=Path(__file__).resolve().parents[1]
with (ROOT/"data/productos.csv").open(encoding="utf-8-sig",newline="") as f:
    products=list(csv.DictReader(f))
company=json.loads((ROOT/"data/empresa.json").read_text(encoding="utf-8"))
tax=json.loads((ROOT/"data/categorias.json").read_text(encoding="utf-8"))
errors=[]
if len(products)!=company["productos_activos"]: errors.append("product count differs from company metadata")
ids=[p["product_id"] for p in products]
if len(ids)!=len(set(ids)): errors.append("duplicate product_id")
if any(not p["url"].startswith("https://regalospremium.cl/") for p in products): errors.append("non-canonical host detected")
classified=sum(bool(p["familia"]) for p in products)
review=sum(p["classification_status"]=="REVIEW_UNCLASSIFIED" for p in products)
if classified+review!=len(products): errors.append("classification accounting mismatch")
if review!=tax["productos_en_revision"]: errors.append("review count differs from taxonomy")
family_pairs={(p["macroarea"],p["familia"]) for p in products if p["familia"]}
if len(family_pairs)!=tax["familias_reales"]: errors.append("family count differs from taxonomy")
url_counts=collections.Counter(p["url"] for p in products)
dups=[(u,n) for u,n in url_counts.items() if n>1]
print(f"products={len(products)} families={len(family_pairs)} review={review} unique_urls={len(url_counts)}")
if dups:
    print(f"WARNING: {len(dups)} pre-existing duplicate URL values", file=sys.stderr)
for e in errors: print("ERROR:",e,file=sys.stderr)
sys.exit(1 if errors else 0)
