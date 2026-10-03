import urllib.request, urllib.error, json, re, pathlib
from bs4 import BeautifulSoup
urls=[
"https://regalospremium.cl/botellas-metalicas-publicitarias/botella-termica-ally-acabado-mate.html",
"https://regalospremium.cl/mugs-botellas-termos/botella-termica-dos-tapas-500ml-personalizada.html",
"https://regalospremium.cl/mugs-botellas-termos/taza-con-cierre-mika.html",
]
rows=[]
for u in urls:
    req=urllib.request.Request(u,headers={"User-Agent":"Mozilla/5.0"})
    with urllib.request.urlopen(req,timeout=30) as r:
        body=r.read().decode("utf-8","replace"); status=r.status; final=r.geturl()
    s=BeautifulSoup(body,"html.parser")
    ld=[]
    for x in s.find_all("script",attrs={"type":"application/ld+json"}):
        txt=(x.string or x.get_text()).strip()
        try: d=json.loads(txt)
        except Exception: d={"parse_error":txt[:200]}
        ld.append(d)
    def walk_types(o):
        types=[]
        if isinstance(o,dict):
            t=o.get("@type")
            if isinstance(t,str): types.append(t)
            elif isinstance(t,list): types.extend([x for x in t if isinstance(x,str)])
            for v in o.values(): types.extend(walk_types(v))
        elif isinstance(o,list):
            for v in o: types.extend(walk_types(v))
        return types
    ldtypes=[]
    for d in ld: ldtypes.extend(walk_types(d))
    micro=[x.get("itemtype") for x in s.find_all(attrs={"itemtype":True}) if "schema.org/Product" in x.get("itemtype","") or "schema.org/Offer" in x.get("itemtype","")]
    h1=s.find("h1")
    row={"url":u,"status":status,"final":final,"h1":h1.get_text(" ",strip=True)[:150] if h1 else None,
         "ld_types":ldtypes,"product_jsonld_count":sum(t=="Product" for t in ldtypes),"offer_jsonld_count":sum(t=="Offer" for t in ldtypes),
         "product_offer_microdata":micro,"product_offer_microdata_count":len(micro)}
    rows.append(row); print(json.dumps(row,ensure_ascii=False),flush=True)
pathlib.Path("/home/maxdaguzan/regalospremium-dataset/reports/seo/gsc_schema_b2b_qa_20261003.json").write_text(json.dumps(rows,ensure_ascii=False,indent=2)+"\n")
bad=sum(r["status"]!=200 or r["product_jsonld_count"] or r["offer_jsonld_count"] or r["product_offer_microdata_count"] for r in rows)
print("QA_BAD",bad)
raise SystemExit(1 if bad else 0)
