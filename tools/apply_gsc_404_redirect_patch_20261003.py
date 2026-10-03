from pathlib import Path
import csv, hashlib, shutil, datetime

live=Path("/home/maxdaguzan/RegalosPremium_Backups/gsc_fix_20261003/.htaccess.live")
out=Path("/home/maxdaguzan/RegalosPremium_Backups/gsc_fix_20261003/.htaccess.gscfix")
registry=Path("/home/maxdaguzan/regalospremium-dataset/data/seo_redirects.csv")
regbak=Path("/home/maxdaguzan/RegalosPremium_Backups/gsc_fix_20261003/seo_redirects.csv.before")

text=live.read_text(encoding="utf-8")
block=r'''
# BEGIN GSC SURGERY 2026-10-03
# Exact legacy URLs from GSC Coverage export. Specific rules precede generic Bamboo rule.
RewriteRule ^bolsos-y-mochilas-publicitarios/mochila-picnic\.html$ https://regalospremium.cl/mochilas/mochila-picnic-4-personas-accesorios-cooler.html [R=301,L,NE]
RewriteRule ^publicitarios-belleza-y-salud/deluxe-billetera-de-cuero-color-cafe-\.html$ https://regalospremium.cl/billeteras-y-porta-documentos/billetera-deluxe-cuero-marron-broche.html [R=301,L,NE]
RewriteRule ^bolsas-publicitarias-con-logotipo/bolsa-algodon-manijas-colores-reutilizable\.html$ https://regalospremium.cl/bolsas-de-algodon-publicitarias/bolsa-algodon-asas-colores.html [R=301,L,NE]
RewriteRule ^regalos-publicitarios-para-viajes-y-vacaciones/mesa-plegable-de-picnic\.html$ https://regalospremium.cl/regalos-publicitarios-para-viajes-y-vacaciones/ [R=301,L,NE]
RewriteRule ^publicitarios-bamboo/set-escritura-bambu-boligrafo-portaminas-deluxe\.html$ https://regalospremium.cl/regalos-corporativos-bambu/ [R=301,L,NE]
RewriteRule ^regalos-corporativos-bambu/set-escritura-bambu-boligrafo-portaminas-deluxe\.html$ https://regalospremium.cl/regalos-corporativos-bambu/ [R=301,L,NE]
RewriteRule ^bolsos-y-mochilas-publicitarios/mochila-netech\.html$ https://regalospremium.cl/bolsos-y-mochilas-publicitarios/ [R=301,L,NE]
RewriteRule ^boligrafos-metalicos-y-ejecutivos/boligrafo-negro-cobre-tinta-azul\.html$ https://regalospremium.cl/boligrafos-metalicos-y-ejecutivos-publicitarios/ [R=301,L,NE]
RewriteRule ^publicitarios-ecofriendly/llavero-linterna-led-dinamo\.html$ https://regalospremium.cl/llaveros-promocionales/llavero-linterna-led.html [R=301,L,NE]
RewriteRule ^publicitarios-bamboo/pendrive-4gb-de-bamboo\.html$ https://regalospremium.cl/regalos-corporativos-bambu/ [R=301,L,NE]
RewriteRule ^regalos-corporativos-bambu/pendrive-4gb-de-bamboo\.html$ https://regalospremium.cl/regalos-corporativos-bambu/ [R=301,L,NE]
# Category intentionally retired with no equivalent landing; return explicit Gone instead of an ambiguous soft redirect.
RewriteRule ^merchandising-masivo/?$ - [R=410,L]
# END GSC SURGERY 2026-10-03

'''
if "# BEGIN GSC SURGERY 2026-10-03" in text:
    raise SystemExit("PATCH_ALREADY_PRESENT")
needle="# Consolidacion Bamboo 2026-09-30: una sola familia canonica"
if needle not in text:
    raise SystemExit("INSERTION_MARKER_NOT_FOUND")
patched=text.replace(needle,block+needle,1)
out.write_text(patched,encoding="utf-8")
shutil.copy2(registry,regbak)

rows=[]
with registry.open(encoding="utf-8-sig",newline="") as f:
    rows=list(csv.DictReader(f))
fields=["old_url","new_url","http_code","status","effective_date","reason"]
adds=[
("https://regalospremium.cl/bolsos-y-mochilas-publicitarios/mochila-picnic.html","https://regalospremium.cl/mochilas/mochila-picnic-4-personas-accesorios-cooler.html","301","APPLIED","2026-10-03","GSC 404: reemplazo semántico activo"),
("https://regalospremium.cl/publicitarios-belleza-y-salud/deluxe-billetera-de-cuero-color-cafe-.html","https://regalospremium.cl/billeteras-y-porta-documentos/billetera-deluxe-cuero-marron-broche.html","301","APPLIED","2026-10-03","GSC 404: sucesor semántico activo"),
("https://regalospremium.cl/bolsas-publicitarias-con-logotipo/bolsa-algodon-manijas-colores-reutilizable.html","https://regalospremium.cl/bolsas-de-algodon-publicitarias/bolsa-algodon-asas-colores.html","301","APPLIED","2026-10-03","GSC 404: sucesor semántico activo"),
("https://regalospremium.cl/regalos-publicitarios-para-viajes-y-vacaciones/mesa-plegable-de-picnic.html","https://regalospremium.cl/regalos-publicitarios-para-viajes-y-vacaciones/","301","APPLIED","2026-10-03","GSC 404: producto retirado a categoría activa"),
("https://regalospremium.cl/publicitarios-bamboo/set-escritura-bambu-boligrafo-portaminas-deluxe.html","https://regalospremium.cl/regalos-corporativos-bambu/","301","APPLIED","2026-10-03","GSC 404: evita cadena Bamboo a 404"),
("https://regalospremium.cl/regalos-corporativos-bambu/set-escritura-bambu-boligrafo-portaminas-deluxe.html","https://regalospremium.cl/regalos-corporativos-bambu/","301","APPLIED","2026-10-03","GSC 404: destino intermedio retirado"),
("https://regalospremium.cl/bolsos-y-mochilas-publicitarios/mochila-netech.html","https://regalospremium.cl/bolsos-y-mochilas-publicitarios/","301","APPLIED","2026-10-03","GSC 404: producto retirado a categoría activa"),
("https://regalospremium.cl/boligrafos-metalicos-y-ejecutivos/boligrafo-negro-cobre-tinta-azul.html","https://regalospremium.cl/boligrafos-metalicos-y-ejecutivos-publicitarios/","301","APPLIED","2026-10-03","GSC 404: ruta antigua a categoría canónica activa"),
("https://regalospremium.cl/publicitarios-ecofriendly/llavero-linterna-led-dinamo.html","https://regalospremium.cl/llaveros-promocionales/llavero-linterna-led.html","301","APPLIED","2026-10-03","GSC 404: reemplazo funcional activo"),
("https://regalospremium.cl/publicitarios-bamboo/pendrive-4gb-de-bamboo.html","https://regalospremium.cl/regalos-corporativos-bambu/","301","APPLIED","2026-10-03","GSC 404: producto retirado a hub Bamboo"),
("https://regalospremium.cl/regalos-corporativos-bambu/pendrive-4gb-de-bamboo.html","https://regalospremium.cl/regalos-corporativos-bambu/","301","APPLIED","2026-10-03","GSC 404: evita destino intermedio 404"),
("https://regalospremium.cl/merchandising-masivo/","","410","APPLIED","2026-10-03","GSC 404: categoría retirada sin equivalente; Gone explícito"),
]
by_old={r["old_url"]:r for r in rows}
for a in adds:
    d=dict(zip(fields,a)); by_old[d["old_url"]]=d
ordered=list(rows)
existing={r["old_url"] for r in rows}
for a in adds:
    d=dict(zip(fields,a))
    if d["old_url"] not in existing: ordered.append(d)
    else:
        for i,r in enumerate(ordered):
            if r["old_url"]==d["old_url"]: ordered[i]=d
with registry.open("w",encoding="utf-8",newline="") as f:
    w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(ordered)

for p in (live,out,registry,regbak):
    b=p.read_bytes()
    print(p, len(b), hashlib.sha256(b).hexdigest())
