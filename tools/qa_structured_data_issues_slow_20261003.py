import csv,json,pathlib,subprocess,time
from bs4 import BeautifulSoup
SRC="/home/maxdaguzan/regalospremium-dataset/data/gsc/structured_data_issues_20261003.csv"
OUT="/home/maxdaguzan/regalospremium-dataset/reports/seo/gsc_structured_data_qa_slow_20261003.json"
with open(SRC,encoding="utf-8-sig") as f: rows=list(csv.DictReader(f))
def walk(o):
    z=[]
    if isinstance(o,dict):
        t=o.get("@type")
        if isinstance(t,str): z.append(t)
        elif isinstance(t,list): z += [x for x in t if isinstance(x,str)]
        for v in o.values(): z+=walk(v)
    elif isinstance(o,list):
        for v in o: z+=walk(v)
    return z
out=[]; bad=0
for i,r in enumerate(rows,1):
    p=subprocess.run(["curl","-sS","-L","--max-time","15","-A","Mozilla/5.0 (compatible; RP-QA/1.0)","-w","\n__META__%{http_code}|%{url_effective}",r["url"]],capture_output=True,text=True,timeout=20)
    body,_,meta=p.stdout.rpartition("\n__META__")
    a=meta.split("|",1); status=int(a[0] or 0) if a else 0; final=a[1] if len(a)>1 else ""
    s=BeautifulSoup(body,"html.parser"); types=[]; perr=0
    for x in s.find_all("script",attrs={"type":"application/ld+json"}):
        txt=(x.string or x.get_text()).strip()
        if not txt: continue
        try: types+=walk(json.loads(txt))
        except Exception: perr+=1
    micro=[x.get("itemtype") for x in s.find_all(attrs={"itemtype":True}) if "schema.org/Product" in x.get("itemtype","") or "schema.org/Offer" in x.get("itemtype","")]
    ok=status==200 and "Product" not in types and "Offer" not in types and len(micro)==0 and perr==0
    x={**r,"status":status,"final_url":final,"ld_types":sorted(set(types)),"product_jsonld":types.count("Product"),"offer_jsonld":types.count("Offer"),"product_offer_microdata_count":len(micro),"jsonld_parse_errors":perr,"ok":ok}
    out.append(x); bad+=0 if ok else 1
    print(f"{i:02d}/17 status={status} product={x['product_jsonld']} offer={x['offer_jsonld']} micro={len(micro)} ok={ok} {r['url']}",flush=True)
    time.sleep(1.2)
pathlib.Path(OUT).write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("TOTAL",len(out),"PASS",len(out)-bad,"FAIL",bad)
raise SystemExit(1 if bad else 0)
