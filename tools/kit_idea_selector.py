#!/usr/bin/env python3
from flask import Flask, request, render_template_string, url_for
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from pathlib import Path
from collections import Counter, defaultdict
import requests, json, re, sqlite3, concurrent.futures, time

ROOT=Path("/home/maxdaguzan/regalospremium-dataset")
SRC=ROOT/"data/seo/kit_competitor_sources.json"
DB=ROOT/"var/ecosystem.db"
OUT_JSON=ROOT/"reports/seo/kit_idea_selector_latest.json"
OUT_MD=ROOT/"reports/seo/kit_idea_selector_latest.md"
PORT=8791
app=Flask(__name__)

KIT_LABELS={
 "welcome":"Kits de bienvenida para empresas",
 "remote":"Kits de trabajo remoto",
 "recognition":"Kits de reconocimiento",
 "technology":"Kits de tecnología",
 "identification":"Kits de identificación",
 "executive":"Kits ejecutivos",
}

PRODUCT_TERMS={
 "mochila":["mochila","backpack"],
 "bolso":["bolso","maletin","maletín","bag"],
 "botella":["botella","bottle"],
 "mug":["mug","taza","vaso"],
 "termo":["termo","termica","térmica"],
 "libreta":["libreta","cuaderno","notebook"],
 "bolígrafo":["boligrafo","bolígrafo","lapiz","lápiz","pen"],
 "power bank":["power bank","powerbank","bateria externa","batería externa"],
 "audífonos":["audifonos","audífonos","auriculares","headphones"],
 "cargador":["cargador","charger"],
 "cable":["cable","adaptador"],
 "soporte móvil":["soporte celular","soporte movil","soporte móvil","stand"],
 "organizador":["organizador","organizer"],
 "carpeta":["carpeta","portafolio"],
 "tarjetero":["tarjetero","porta tarjetas","portatarjetas","rfid"],
 "lanyard":["lanyard","porta credencial","portacredencial","credencial"],
 "llavero":["llavero","keychain"],
 "parlante":["parlante","altavoz","speaker"],
 "mouse":["mouse","ratón"],
 "teclado":["teclado","keyboard"],
 "hub USB":["hub usb","usb hub"],
 "estuche":["estuche","case"],
 "caja premium":["caja de regalo","caja premium","gift box"],
 "stickers":["sticker","stickers"],
}

KIT_CORE={
 "welcome":["mochila","botella","libreta","bolígrafo","lanyard"],
 "remote":["mochila","power bank","cargador","cable","soporte móvil","libreta","mug"],
 "recognition":["termo","libreta","bolígrafo","carpeta","caja premium"],
 "technology":["power bank","cargador","cable","audífonos","parlante","soporte móvil","hub USB"],
 "identification":["lanyard","tarjetero","llavero","estuche","bolígrafo"],
 "executive":["carpeta","libreta","bolígrafo","termo","bolso","tarjetero"],
}

IDEA_RULES={
 "welcome":[("Ingreso esencial","Uso diario + identidad + bienvenida."),("Bienvenida sustentable","Reutilizables + libreta + empaque simple."),("Primer día premium","Pieza ejecutiva + hidratación + escritura.")],
 "remote":[("Home office esencial","Soporte + carga + escritura + hidratación."),("Movilidad híbrida","Mochila/bolso + energía + conectividad."),("Escritorio compacto","Organización + soporte + periféricos ligeros.")],
 "recognition":[("Hito laboral","Pieza durable + personalización individual."),("Reconocimiento de equipo","Set homogéneo con nombre/cargo."),("Cliente destacado","Producto ejecutivo + presentación especial.")],
 "technology":[("Carga y conectividad","Energía + cables + soporte."),("Audio y movilidad","Audio + carga + estuche."),("Escritorio digital","Hub/soporte + periférico + organización.")],
 "identification":[("Acceso diario","Lanyard + credencial + tarjetero."),("Terreno","Identificación resistente + llavero + estuche."),("Identidad ejecutiva","Tarjetero + lanyard sobrio + escritura.")],
 "executive":[("Reunión ejecutiva","Carpeta + libreta + bolígrafo."),("Movilidad profesional","Bolso + energía + tarjetero."),("Cliente VIP","Pieza premium + bebida + presentación.")],
}

HTML="""<!doctype html><html lang="es"><head><meta charset="utf-8">
<title>Selector Automático de Kits RP</title>
<style>
body{font-family:system-ui;margin:0;background:#f4f6f8;color:#17212b}.wrap{max-width:1280px;margin:22px auto;padding:0 18px}
h1{margin:0 0 4px}.sub{color:#66717d;margin-bottom:18px}.nav{display:flex;gap:8px;flex-wrap:wrap;margin:12px 0 18px}
.nav a{background:#fff;border:1px solid #ccd4dd;padding:9px 12px;border-radius:8px;text-decoration:none;color:#173f6d}
.card{background:#fff;border:1px solid #dfe4ea;border-radius:12px;padding:16px;margin-bottom:16px;box-shadow:0 1px 3px #0001}
.kit{border-left:5px solid #5d6d7e}.cols{display:grid;grid-template-columns:1.05fr .95fr;gap:16px}.tag{display:inline-block;padding:4px 8px;margin:3px;border-radius:99px;background:#eef2f6}
.src{font-size:13px;padding:4px 0}.ok{color:#146b2e}.err{color:#a1342d}.product{padding:7px 0;border-bottom:1px solid #eee}.muted{font-size:13px;color:#68737f}
.bundle{background:#f8fafc;border:1px solid #e4e9ef;border-radius:8px;padding:10px;margin:8px 0}a{color:#164d8f}
table{width:100%;border-collapse:collapse}td,th{padding:7px;border-bottom:1px solid #e7ebef;text-align:left;vertical-align:top}
@media(max-width:850px){.cols{grid-template-columns:1fr}}
</style></head><body><div class="wrap">
<h1>Selector automático de kits corporativos</h1>
<div class="sub">Analiza las referencias configuradas, extrae patrones funcionales y los cruza con productos activos de Regalos Premium. No copia textos ni kits completos.</div>
<div class="nav">
<a href="/auto-all">Actualizar las 6 familias</a>
{% for k,v in labels.items() %}<a href="/auto?kit={{k}}">{{v}}</a>{% endfor %}
</div>
{% if summary %}<div class="card"><b>Última corrida:</b> {{summary}}</div>{% endif %}
{% for kit in kits %}
<div class="card kit">
<h2>{{kit.label}}</h2>
<div class="cols">
<div>
<h3>Qué está usando la competencia</h3>
{% for t,n in kit.terms %}<span class="tag">{{t}} ({{n}})</span>{% endfor %}
{% if not kit.terms %}<p class="muted">No se detectaron conceptos reutilizables en las fuentes accesibles.</p>{% endif %}
<h3>Fuentes analizadas</h3>
{% for s in kit.sources %}<div class="src"><span class="{{'ok' if s.ok else 'err'}}">{{'PASS' if s.ok else 'FAIL'}}</span> · <a href="{{s.url}}" target="_blank">{{s.domain}}</a> · {{s.status}}</div>{% endfor %}
<h3>Ideas propias RP</h3>
{% for a,b in kit.ideas %}<div class="bundle"><b>{{a}}</b><br>{{b}}</div>{% endfor %}
</div>
<div>
<h3>Productos RP candidatos</h3>
{% for term,products in kit.candidates.items() %}
{% if products %}
<div class="bundle"><b>{{term}}</b>
{% for p in products %}<div class="product">{{p.reference or 's/ref'}} · <a href="{{p.url}}" target="_blank">{{p.name}}</a></div>{% endfor %}
</div>
{% endif %}
{% endfor %}
<h3>Combinaciones automáticas</h3>
{% for b in kit.bundles %}<div class="bundle"><b>{{b.name}}</b><br>{% for x in b["items"] %}{{x}}{% if not loop.last %} + {% endif %}{% endfor %}</div>{% endfor %}
</div>
</div>
</div>
{% endfor %}
</div></body></html>"""

def load_sources():
    return json.loads(SRC.read_text(encoding="utf-8"))

def fetch_concepts(url):
    if not url.startswith(("http://","https://")):
        return {"url":url,"ok":False,"status":"URL inválida","terms":[],"domain":"","title":""}
    try:
        r=requests.get(url,timeout=15,headers={"User-Agent":"Mozilla/5.0 (compatible; RP-Kit-Research/2.0)"})
        r.raise_for_status()
    except Exception as e:
        return {"url":url,"ok":False,"status":type(e).__name__,"terms":[],"domain":urlparse(url).netloc,"title":""}
    soup=BeautifulSoup(r.text,"html.parser")
    for x in soup(["script","style","noscript"]): x.decompose()
    title=(soup.title.get_text(" ",strip=True) if soup.title else "")[:140]
    text=" ".join(x.get_text(" ",strip=True) for x in soup.find_all(["h1","h2","h3","li","p","a"]))
    text=re.sub(r"\s+"," ",text).lower()
    terms=[]
    for label,variants in PRODUCT_TERMS.items():
        if any(v in text for v in variants): terms.append(label)
    return {"url":url,"ok":True,"status":f"HTTP {r.status_code} · {len(terms)} conceptos","terms":terms,"domain":urlparse(url).netloc,"title":title}

def catalog_candidates(term,limit=3):
    variants=PRODUCT_TERMS.get(term,[term])
    con=sqlite3.connect(DB); con.row_factory=sqlite3.Row
    rows=con.execute("""select product_id,reference,name,prestashop_candidate_url,default_category_name
                        from products where active=1 and indexed=1""").fetchall()
    con.close()
    scored=[]
    for r in rows:
        hay=(" ".join([r["name"] or "",r["default_category_name"] or ""])).lower()
        score=sum(3 for v in variants if v.lower() in (r["name"] or "").lower()) + sum(1 for v in variants if v.lower() in hay)
        if score:
            scored.append((score,dict(r)))
    scored.sort(key=lambda x:(-x[0],x[1]["name"].lower()))
    return [{"reference":x[1]["reference"],"name":x[1]["name"],"url":x[1]["prestashop_candidate_url"] or ""} for x in scored[:limit]]

def build_bundles(kit,candidates,terms):
    preferred=[t for t,_ in terms] + KIT_CORE.get(kit,[])
    seen=[]; ordered=[]
    for t in preferred:
        if t not in seen and candidates.get(t):
            ordered.append(t); seen.append(t)
    bundles=[]
    offsets=[0,1,2]
    for bi,off in enumerate(offsets,1):
        items=[]
        for t in ordered[:5]:
            ps=candidates.get(t,[])
            if ps:
                p=ps[min(off,len(ps)-1)]
                items.append(f"{p['reference'] or 's/ref'} {p['name']}")
            if len(items)>=4: break
        if items: bundles.append({"name":f"Propuesta {bi}","items":items})
    return bundles

def analyze_kit(kit,source_map,cache):
    refs=source_map.get(kit,[])
    results=[cache[s["url"]] for s in refs]
    count=Counter()
    for r in results:
        if r["ok"]: count.update(r["terms"])
    # competition signals first; core terms ensure useful local candidates even if a site blocks crawling
    ordered_terms=[t for t,_ in count.most_common()] + [t for t in KIT_CORE.get(kit,[]) if t not in count]
    candidates={t:catalog_candidates(t,3) for t in ordered_terms[:10]}
    ideas=list(IDEA_RULES.get(kit,[]))
    if count:
        top=", ".join(t for t,_ in count.most_common(5))
        ideas.insert(0,("Patrón observado",f"La competencia repite {top}. RP puede recombinar esos usos con productos propios, sin replicar su set ni su redacción."))
    return {
      "kit":kit,"label":KIT_LABELS[kit],"terms":count.most_common(12),"sources":results,
      "ideas":ideas,"candidates":candidates,"bundles":build_bundles(kit,candidates,count.most_common())
    }

def run_all(selected=None):
    src=load_sources()
    kits=[selected] if selected else list(KIT_LABELS)
    urls=sorted({s["url"] for k in kits for s in src.get(k,[])})
    cache={}
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
        fut={ex.submit(fetch_concepts,u):u for u in urls}
        for f in concurrent.futures.as_completed(fut):
            cache[fut[f]]=f.result()
    data=[analyze_kit(k,src,cache) for k in kits]
    payload={"generated_at":time.strftime("%Y-%m-%d %H:%M:%S"),"kits":data}
    OUT_JSON.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    md=["# Selector automático de kits RP",f"Generado: {payload['generated_at']}",""]
    for k in data:
        md += [f"## {k['label']}","", "Señales: "+", ".join(f"{t}({n})" for t,n in k["terms"]) if k["terms"] else "Señales: sin extracción útil",""]
        for b in k["bundles"]: md += [f"- **{b['name']}**: "+" + ".join(b["items"])]
        md.append("")
    OUT_MD.write_text("\n".join(md)+"\n",encoding="utf-8")
    return data,payload["generated_at"]

@app.route("/")
def home():
    data,ts=run_all()
    return render_template_string(HTML,kits=data,labels=KIT_LABELS,summary=f"{ts} · análisis automático completo")

@app.route("/auto-all")
def auto_all():
    data,ts=run_all()
    return render_template_string(HTML,kits=data,labels=KIT_LABELS,summary=f"{ts} · 6 familias actualizadas")

@app.route("/auto")
def auto_one():
    kit=request.args.get("kit","welcome")
    if kit not in KIT_LABELS: kit="welcome"
    data,ts=run_all(kit)
    return render_template_string(HTML,kits=data,labels=KIT_LABELS,summary=f"{ts} · {KIT_LABELS[kit]} actualizado")

if __name__=="__main__":
    print(f"RP Kit Idea Selector AUTO: http://127.0.0.1:{PORT}")
    app.run(host="127.0.0.1",port=PORT,debug=False)
