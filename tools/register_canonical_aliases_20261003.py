from pathlib import Path
import csv
p=Path("/home/maxdaguzan/regalospremium-dataset/data/seo_redirects.csv")
fields=["old_url","new_url","http_code","status","effective_date","reason"]
with p.open(encoding="utf-8-sig",newline="") as f:
    rows=list(csv.DictReader(f))
adds=[
("https://regalospremium.cl/publicitarios-ecofriendly/","https://regalospremium.cl/productos-eco-friendly-publicitarios/","301","APPLIED","2026-10-03","GSC canonical-alternate: alias legacy a categoría canónica"),
("https://regalospremium.cl/boligrafos-funcionales-y-destacadores/","https://regalospremium.cl/boligrafos-funcionales-y-destacadores-publicitarios/","301","APPLIED","2026-10-03","GSC canonical-alternate: alias legacy a categoría canónica"),
("https://regalospremium.cl/boligrafos-cuerpo-blanco/","https://regalospremium.cl/boligrafos-cuerpo-blanco-publicitarios/","301","APPLIED","2026-10-03","GSC canonical-alternate: alias legacy a categoría canónica"),
("https://regalospremium.cl/mugs-termos-sublimacion/","https://regalospremium.cl/mugs-y-termos-para-sublimacion-publicitarios/","301","APPLIED","2026-10-03","GSC canonical-alternate: alias legacy a categoría canónica"),
("https://regalospremium.cl/boligrafos-cuerpo-color/","https://regalospremium.cl/boligrafos-cuerpo-color-publicitarios/","301","APPLIED","2026-10-03","GSC canonical-alternate: alias legacy a categoría canónica"),
("https://regalospremium.cl/boligrafos-cuerpo-plateado/","https://regalospremium.cl/boligrafos-cuerpo-plateado-publicitarios/","301","APPLIED","2026-10-03","GSC canonical-alternate: alias legacy a categoría canónica"),
]
by={r["old_url"]:r for r in rows}
for a in adds:
    d=dict(zip(fields,a)); by[d["old_url"]]=d
out=[]; seen=set()
for r in rows:
    u=r["old_url"]
    if u in by and u not in seen:
        out.append(by[u]); seen.add(u)
for a in adds:
    d=dict(zip(fields,a))
    if d["old_url"] not in seen:
        out.append(d); seen.add(d["old_url"])
with p.open("w",encoding="utf-8",newline="\n") as f:
    w=csv.DictWriter(f,fieldnames=fields,lineterminator="\n"); w.writeheader(); w.writerows(out)
print("ROWS",len(out))
