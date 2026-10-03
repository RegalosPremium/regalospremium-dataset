import subprocess, json, sys, pathlib
cases=[
("https://regalospremium.cl/bolsos-y-mochilas-publicitarios/mochila-picnic.html",301,200,"https://regalospremium.cl/mochilas/mochila-picnic-4-personas-accesorios-cooler.html"),
("https://regalospremium.cl/publicitarios-belleza-y-salud/deluxe-billetera-de-cuero-color-cafe-.html",301,200,"https://regalospremium.cl/billeteras-y-porta-documentos/billetera-deluxe-cuero-marron-broche.html"),
("https://regalospremium.cl/bolsas-publicitarias-con-logotipo/bolsa-algodon-manijas-colores-reutilizable.html",301,200,"https://regalospremium.cl/bolsas-de-algodon-publicitarias/bolsa-algodon-asas-colores.html"),
("https://regalospremium.cl/regalos-publicitarios-para-viajes-y-vacaciones/mesa-plegable-de-picnic.html",301,200,"https://regalospremium.cl/regalos-publicitarios-para-viajes-y-vacaciones/"),
("https://regalospremium.cl/publicitarios-bamboo/set-escritura-bambu-boligrafo-portaminas-deluxe.html",301,200,"https://regalospremium.cl/regalos-corporativos-bambu/"),
("https://regalospremium.cl/merchandising-masivo/",404,404,"https://regalospremium.cl/merchandising-masivo/"),
("https://regalospremium.cl/bolsos-y-mochilas-publicitarios/mochila-netech.html",301,200,"https://regalospremium.cl/bolsos-y-mochilas-publicitarios/"),
("https://regalospremium.cl/boligrafos-metalicos-y-ejecutivos/boligrafo-negro-cobre-tinta-azul.html",301,200,"https://regalospremium.cl/boligrafos-metalicos-y-ejecutivos-publicitarios/"),
("https://regalospremium.cl/regalos-publicitarios-para-invierno/",200,200,"https://regalospremium.cl/regalos-publicitarios-para-invierno/"),
("https://regalospremium.cl/publicitarios-ecofriendly/llavero-linterna-led-dinamo.html",301,200,"https://regalospremium.cl/llaveros-promocionales/llavero-linterna-led.html"),
("https://regalospremium.cl/publicitarios-bamboo/pendrive-4gb-de-bamboo.html",301,200,"https://regalospremium.cl/regalos-corporativos-bambu/"),
]
def run(cmd):
    p=subprocess.run(cmd,capture_output=True,text=True,timeout=15)
    return p.returncode,p.stdout.strip(),p.stderr.strip()
rows=[]; bad=0
for url,expect_first,expect_final,expect_url in cases:
    rc,out,err=run(["curl","-sS","-o","/dev/null","--max-time","10","-w","%{http_code}|%{redirect_url}",url])
    first_s,loc=(out.split("|",1)+[""])[:2]
    first=int(first_s or 0)
    rc2,out2,err2=run(["curl","-sS","-L","-o","/dev/null","--max-time","12","-w","%{http_code}|%{url_effective}",url])
    fin_s,finurl=(out2.split("|",1)+[""])[:2]
    final=int(fin_s or 0)
    ok=first==expect_first and final==expect_final and (expect_final==404 or finurl.rstrip("/")==expect_url.rstrip("/"))
    if not ok: bad+=1
    row={"url":url,"first":first,"location":loc,"final":final,"final_url":finurl,"expected_first":expect_first,"expected_final":expect_final,"expected_url":expect_url,"ok":ok,"error":err or err2}
    rows.append(row); print(json.dumps(row,ensure_ascii=False),flush=True)
# Site sanity
for url in ["https://regalospremium.cl/","https://regalospremium.cl/1_index_sitemap.xml","https://regalospremium.cl/robots.txt"]:
    rc,out,err=run(["curl","-sS","-L","-o","/dev/null","--max-time","12","-w","%{http_code}",url])
    ok=out=="200"; bad+=0 if ok else 1
    row={"url":url,"final":int(out or 0),"ok":ok,"error":err}; rows.append(row); print(json.dumps(row,ensure_ascii=False),flush=True)
path=pathlib.Path("/home/maxdaguzan/regalospremium-dataset/reports/seo/gsc_fix_qa_20261003.json")
path.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("QA_BAD",bad)
sys.exit(1 if bad else 0)
