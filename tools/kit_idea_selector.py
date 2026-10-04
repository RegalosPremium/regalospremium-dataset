#!/usr/bin/env python3
from flask import Flask, request, render_template_string, redirect, url_for
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from pathlib import Path
import requests, json, re, time

ROOT=Path("/home/maxdaguzan/regalospremium-dataset")
SRC=ROOT/"data/seo/kit_competitor_sources.json"
CACHE=ROOT/"var/kit_idea_selector_cache.json"
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
 "bolso":["bolso","bag"],
 "botella":["botella","bottle"],
 "mug":["mug","taza","vaso"],
 "termo":["termo","termica","térmica"],
 "libreta":["libreta","cuaderno","notebook"],
 "bolígrafo":["boligrafo","bolígrafo","lapiz","lápiz","pen"],
 "power bank":["power bank","bateria externa","batería externa"],
 "audífonos":["audifonos","audífonos","auriculares","headphones"],
 "cargador":["cargador","charger"],
 "cable":["cable","adaptador"],
 "soporte móvil":["soporte","stand"],
 "organizador":["organizador","organizer"],
 "carpeta":["carpeta","portafolio"],
 "tarjetero":["tarjetero","porta tarjetas","rfid"],
 "lanyard":["lanyard","porta credencial","credencial"],
 "llavero":["llavero","keychain"],
 "parlante":["parlante","altavoz","speaker"],
 "mouse":["mouse","ratón"],
 "teclado":["teclado","keyboard"],
 "hub USB":["hub usb","usb hub"],
 "estuche":["estuche","case"],
 "caja premium":["caja de regalo","caja premium","gift box"],
 "stickers":["sticker","stickers"],
}

IDEA_RULES={
 "welcome":[
  ("Inicio útil","Combinar 3–4 objetos de uso diario y una pieza de identidad corporativa."),
  ("Cultura de empresa","Agregar una tarjeta/elemento con valores, bienvenida o guía de primer día."),
  ("Sustentable","Priorizar botella reutilizable, libreta reciclada y empaque de bajo residuo."),
 ],
 "remote":[
  ("Home office esencial","Soporte de celular + libreta + mug/botella + accesorio de carga."),
  ("Movilidad híbrida","Mochila o bolso + power bank + cable/adaptador + libreta."),
  ("Ergonomía ligera","Organizador + soporte móvil + accesorios compactos de escritorio."),
 ],
 "recognition":[
  ("Hito laboral","Objeto premium duradero + pieza personalizada + presentación especial."),
  ("Reconocimiento de equipo","Set útil y homogéneo con opción de nombre individual."),
  ("Cliente/colaborador destacado","Producto ejecutivo + empaque + mensaje de agradecimiento."),
 ],
 "technology":[
  ("Carga y conectividad","Power bank + cable/adaptador + soporte móvil."),
  ("Audio y movilidad","Audífonos/parlante + cargador + estuche."),
  ("Escritorio digital","Hub USB + soporte + mouse + organizador."),
 ],
 "identification":[
  ("Acceso diario","Lanyard + porta credencial + tarjetero."),
  ("Terreno y operación","Lanyard resistente + llavero + estuche/documentos."),
  ("Identidad ejecutiva","Tarjetero RFID + lanyard sobrio + bolígrafo."),
 ],
 "executive":[
  ("Reunión ejecutiva","Carpeta/portafolio + libreta + bolígrafo premium."),
  ("Movilidad profesional","Bolso/mochila notebook + power bank + tarjetero."),
  ("Cliente VIP","Objeto de escritorio + bebida premium + caja de presentación."),
 ],
}

HTML="""<!doctype html><html lang="es"><head><meta charset="utf-8">
<title>Selector de Ideas de Kits RP</title>
<style>
body{font-family:system-ui;margin:0;background:#f4f6f8;color:#16202a}.wrap{max-width:1180px;margin:24px auto;padding:0 18px}
h1{margin-bottom:6px}.sub{color:#5b6570;margin-bottom:22px}.grid{display:grid;grid-template-columns:280px 1fr;gap:18px}
.card{background:#fff;border:1px solid #dfe4ea;border-radius:12px;padding:16px;box-shadow:0 1px 3px #0001}
select,input,button{width:100%;box-sizing:border-box;padding:10px;border:1px solid #cbd3dc;border-radius:8px;margin:5px 0 10px}
button{cursor:pointer;font-weight:700}.src{padding:10px 0;border-bottom:1px solid #eee}.tag{display:inline-block;padding:4px 8px;margin:3px;border-radius:99px;background:#eef2f6}
.idea{padding:12px;border-left:4px solid #596777;background:#f8fafc;margin:10px 0}.muted{color:#69737d;font-size:13px}
a{color:#164d8f;text-decoration:none}.ok{color:#146b2e}.err{color:#a1342d}.cols{display:grid;grid-template-columns:1fr 1fr;gap:14px}
@media(max-width:800px){.grid,.cols{grid-template-columns:1fr}}
</style></head><body><div class="wrap">
<h1>Selector de ideas para kits corporativos</h1>
<div class="sub">Observa patrones de la competencia y genera combinaciones propias. No copia textos ni composiciones completas.</div>
<div class="grid">
<div class="card">
<form method="get">
<label>Tipo de kit</label>
<select name="kit" onchange="this.form.submit()">
{% for k,v in labels.items() %}<option value="{{k}}" {% if k==kit %}selected{% endif %}>{{v}}</option>{% endfor %}
</select></form>
<h3>Competidores / referencias</h3>
{% for s in sources %}
<div class="src"><b>{{s.name}}</b><br><a href="{{s.url}}" target="_blank">Ver sitio</a> · <a href="{{url_for('analyze')}}?kit={{kit}}&url={{s.url|urlencode}}">Extraer ideas</a></div>
{% endfor %}
<hr>
<form action="{{url_for('analyze')}}" method="get">
<input type="hidden" name="kit" value="{{kit}}">
<label>Analizar otra URL</label>
<input name="url" placeholder="https://..." required>
<button>Analizar</button>
</form>
</div>
<div>
<div class="card">
<h2>{{labels[kit]}}</h2>
<div class="cols">
<div><h3>Conceptos detectados</h3>
{% if result %}
<p class="{{'ok' if result.ok else 'err'}}">{{result.status}}</p>
{% for t in result.terms %}<span class="tag">{{t}}</span>{% endfor %}
{% else %}<p class="muted">Selecciona una fuente para analizarla.</p>{% endif %}
</div>
<div><h3>Ideas RP derivadas</h3>
{% for title,desc in ideas %}
<div class="idea"><b>{{title}}</b><br>{{desc}}</div>
{% endfor %}
</div>
</div>
{% if result %}
<hr><div class="muted">Fuente: {{result.domain}} · {{result.title}}<br>
Extracción limitada a conceptos y patrones funcionales; no se conserva texto comercial de terceros.</div>
{% endif %}
</div>
<div class="card" style="margin-top:18px">
<h3>Reglas del selector</h3>
<p>1) Detecta familias de productos y usos. 2) Descarta redacción ajena. 3) Recomienda combinaciones nuevas según el tipo de kit. 4) La selección final debe cruzarse con stock, MOQ, técnicas de marcaje y margen RP.</p>
</div>
</div></div></div></body></html>"""

def load_sources():
    return json.loads(SRC.read_text(encoding="utf-8"))

def fetch_concepts(url):
    if not url.startswith(("http://","https://")):
        return {"ok":False,"status":"URL inválida","terms":[],"domain":"","title":""}
    try:
        r=requests.get(url,timeout=15,headers={"User-Agent":"Mozilla/5.0 (compatible; RP-Kit-Idea-Selector/1.0)"})
        r.raise_for_status()
    except Exception as e:
        return {"ok":False,"status":f"No se pudo leer: {type(e).__name__}","terms":[],"domain":urlparse(url).netloc,"title":""}
    soup=BeautifulSoup(r.text,"html.parser")
    for x in soup(["script","style","noscript"]): x.decompose()
    title=(soup.title.get_text(" ",strip=True) if soup.title else "")[:140]
    text=" ".join(x.get_text(" ",strip=True) for x in soup.find_all(["h1","h2","h3","li","p"]))
    text=re.sub(r"\s+"," ",text).lower()
    terms=[]
    for label,variants in PRODUCT_TERMS.items():
        if any(v in text for v in variants): terms.append(label)
    return {"ok":True,"status":f"HTTP {r.status_code} · {len(terms)} conceptos útiles","terms":terms[:20],"domain":urlparse(url).netloc,"title":title}

def ideas_for(kit,terms):
    base=list(IDEA_RULES.get(kit,[]))
    if terms:
        top=", ".join(terms[:5])
        base.insert(0,("Combinación sugerida por señales observadas",f"Usar como inspiración funcional: {top}. Recombinar con catálogo RP y no replicar el set del competidor."))
    return base

@app.route("/")
def home():
    kit=request.args.get("kit","welcome")
    if kit not in KIT_LABELS: kit="welcome"
    return render_template_string(HTML,kit=kit,labels=KIT_LABELS,sources=load_sources().get(kit,[]),result=None,ideas=ideas_for(kit,[]))

@app.route("/analyze")
def analyze():
    kit=request.args.get("kit","welcome")
    if kit not in KIT_LABELS: kit="welcome"
    url=request.args.get("url","").strip()
    result=fetch_concepts(url)
    return render_template_string(HTML,kit=kit,labels=KIT_LABELS,sources=load_sources().get(kit,[]),result=result,ideas=ideas_for(kit,result.get("terms",[])))

if __name__=="__main__":
    print(f"RP Kit Idea Selector: http://127.0.0.1:{PORT}")
    app.run(host="127.0.0.1",port=PORT,debug=False)
