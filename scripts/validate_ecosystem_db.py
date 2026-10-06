#!/usr/bin/env python3
import argparse,csv,json,sqlite3,sys
from pathlib import Path
from urllib.parse import urlsplit
ROOT=Path(__file__).resolve().parents[1]
with (ROOT/'data/ads/ads_campaign_blueprint.csv').open(encoding='utf-8',newline='') as f: expected_blue=len(list(csv.DictReader(f)))
with (ROOT/'data/ads/ads_intent_mapping.csv').open(encoding='utf-8',newline='') as f: expected_kw=len(list(csv.DictReader(f)))
expected_families=json.loads((ROOT/'data/categorias.json').read_text(encoding='utf-8'))['familias_reales']
p=argparse.ArgumentParser();p.add_argument('--db',default=str(ROOT/'var/ecosystem.db'));a=p.parse_args()
c=sqlite3.connect(a.db); errors=[]
def one(q): return c.execute(q).fetchone()[0]
status=c.execute('SELECT status FROM sync_runs ORDER BY run_id DESC LIMIT 1').fetchone()[0]
products=one('SELECT COUNT(*) FROM products'); active=one('SELECT COUNT(*) FROM products WHERE active=1')
tax=one('SELECT COUNT(*) FROM taxonomy_products'); active_catalog=one('SELECT COUNT(*) FROM v_active_catalog')
families=one('SELECT COUNT(DISTINCT family_entity_key) FROM taxonomy_products WHERE family_entity_key IS NOT NULL')
blue=one('SELECT COUNT(*) FROM ads_blueprint'); blue_prod=one("SELECT COUNT(*) FROM ads_blueprint WHERE intent_class='PRODUCTO'")
kw=one('SELECT COUNT(*) FROM ads_keywords'); resolved=one("SELECT COUNT(*) FROM ads_blueprint WHERE intent_class='PRODUCTO' AND resolved_url IS NOT NULL")
drift_ps=one('SELECT COUNT(*) FROM products p LEFT JOIN taxonomy_products t USING(product_id) WHERE p.active=1 AND t.product_id IS NULL')
drift_gh=one('SELECT COUNT(*) FROM taxonomy_products t LEFT JOIN products p USING(product_id) WHERE p.product_id IS NULL OR p.active!=1')
if status!='PASS': errors.append(f'last sync status={status}')
if active!=tax or active_catalog!=active: errors.append('active PrestaShop / taxonomy count mismatch')
if drift_ps or drift_gh: errors.append(f'catalog drift ps={drift_ps} github={drift_gh}')
if families!=expected_families: errors.append(f'family count={families}, expected={expected_families}')
if blue_prod!=expected_families: errors.append(f'product blueprint count={blue_prod}, expected={expected_families}')
if blue!=expected_blue: errors.append(f'blueprint total={blue}, expected={expected_blue}')
if kw!=expected_kw: errors.append(f'ads keyword count={kw}, expected={expected_kw}')
for u, in c.execute('SELECT resolved_url FROM ads_blueprint WHERE resolved_url IS NOT NULL'):
 q=urlsplit(u)
 if q.scheme!='https' or q.netloc!='regalospremium.cl': errors.append(f'bad resolved URL {u}')
anom=one('SELECT COUNT(*) FROM prestashop_anomalies')
unresolved=[r[0] for r in c.execute("SELECT family FROM ads_blueprint WHERE intent_class='PRODUCTO' AND resolved_url IS NULL ORDER BY family")]
print(f'products={products} active={active} taxonomy={tax} families={families} ads_keywords={kw} blueprint={blue} resolved_product_landings={resolved} anomalies={anom}')
print('unresolved_product_families=',', '.join(unresolved) if unresolved else 'NONE')
for e in errors: print('ERROR:',e,file=sys.stderr)
c.close();sys.exit(1 if errors else 0)
