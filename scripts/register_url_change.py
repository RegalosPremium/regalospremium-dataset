#!/usr/bin/env python3
"""Register one approved catalog URL change for the ecosystem synchronizer."""
import argparse, csv, sys
from pathlib import Path
from urllib.parse import urlsplit

ROOT=Path(__file__).resolve().parents[1]
QUEUE=ROOT/'data/url_changes.csv'
PRODUCTS=ROOT/'data/productos.csv'
HOST='regalospremium.cl'
FIELDS=['change_id','product_id','old_url','new_url','effective_date','status','notes']

def valid_url(value):
    p=urlsplit(value)
    return p.scheme=='https' and p.netloc==HOST and bool(p.path)

def main():
    p=argparse.ArgumentParser()
    p.add_argument('change_id'); p.add_argument('product_id'); p.add_argument('old_url'); p.add_argument('new_url')
    p.add_argument('--effective-date', required=True); p.add_argument('--notes', default='')
    a=p.parse_args()
    if not valid_url(a.old_url) or not valid_url(a.new_url) or a.old_url==a.new_url:
        sys.exit('URLs inválidas: deben ser https://regalospremium.cl/... y distintas')
    with PRODUCTS.open(encoding='utf-8-sig',newline='') as f: products=list(csv.DictReader(f))
    product=next((r for r in products if r['product_id']==a.product_id),None)
    if not product: sys.exit(f'product_id inexistente: {a.product_id}')
    with QUEUE.open(encoding='utf-8-sig',newline='') as f: rows=list(csv.DictReader(f))
    if any(r['change_id']==a.change_id for r in rows): sys.exit(f'change_id duplicado: {a.change_id}')
    row={'change_id':a.change_id,'product_id':a.product_id,'old_url':a.old_url,'new_url':a.new_url,
         'effective_date':a.effective_date,'status':'READY','notes':a.notes}
    with QUEUE.open('a',encoding='utf-8',newline='') as f: csv.DictWriter(f,fieldnames=FIELDS).writerow(row)
    print(f"registered {a.change_id} product={a.product_id} status=READY")
if __name__=='__main__': main()
