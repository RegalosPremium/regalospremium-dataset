import os,subprocess,json,urllib.request,urllib.parse,pathlib
SITE="https://regalospremium.cl/"
G="/home/maxdaguzan/.local/gcloud-install/google-cloud-sdk/bin/gcloud"
ENV=dict(os.environ); ENV["CLOUDSDK_CONFIG"]="/home/maxdaguzan/.config/gcloud-rp-explorer"
SA="rp-google-ads-cli@able-marking-493221-m5.iam.gserviceaccount.com"
p=subprocess.run([G,"auth","print-access-token","--impersonate-service-account="+SA,"--scopes=https://www.googleapis.com/auth/webmasters.readonly","--quiet"],env=ENV,capture_output=True,text=True,timeout=60)
if p.returncode or not p.stdout.strip(): raise SystemExit("TOKEN_FAIL:"+(p.stderr[-500:] if p.stderr else "empty"))
tok=p.stdout.strip(); H={"Authorization":"Bearer "+tok,"Content-Type":"application/json"}
siteq=urllib.parse.quote(SITE,safe="")
URL=f"https://www.googleapis.com/webmasters/v3/sites/{siteq}/searchAnalytics/query"
def q(start,end,dimensions=None,rowLimit=25000):
    body={"startDate":start,"endDate":end,"rowLimit":rowLimit}
    if dimensions: body["dimensions"]=dimensions
    req=urllib.request.Request(URL,data=json.dumps(body).encode(),headers=H,method="POST")
    with urllib.request.urlopen(req,timeout=60) as r: return json.load(r)
def agg(d):
    rows=d.get("rows",[])
    if not rows: return {"clicks":0,"impressions":0,"ctr":0,"position":None}
    clicks=sum(x.get("clicks",0) for x in rows); imp=sum(x.get("impressions",0) for x in rows)
    pos=(sum(x.get("position",0)*x.get("impressions",0) for x in rows)/imp) if imp else None
    return {"clicks":clicks,"impressions":imp,"ctr":clicks/imp if imp else 0,"position":pos}
ranges={
 "last_28d_settled":("2026-09-03","2026-09-30"),
 "prev_28d":("2026-08-06","2026-09-02"),
 "sep_1_20":("2026-09-01","2026-09-20"),
 "sep_21_30":("2026-09-21","2026-09-30"),
 "august":("2026-08-01","2026-08-31"),
 "july":("2026-07-01","2026-07-31"),
 "q3_to_sep30":("2026-07-01","2026-09-30"),
 "prev_qtr":("2026-04-01","2026-06-30"),
}
out={"ranges":{}}
for k,(a,b) in ranges.items(): out["ranges"][k]={"start":a,"end":b,**agg(q(a,b))}
for dim in ["query","page"]:
    rows=q("2026-09-03","2026-09-30",[dim],25000).get("rows",[])
    rows=sorted(rows,key=lambda x:(-x.get("impressions",0),x.get("position",999)))
    out["top_"+dim]=rows[:200]
targets=["regalos premium","regalos corporativos premium","regalos publicitarios por mayor","regalos corporativos por mayor","regalos publicitarios","regalos para empresas","regalos corporativos chile","regalos publicitarios chile"]
allq=q("2026-09-03","2026-09-30",["query"],25000).get("rows",[])
m={x["keys"][0].lower():x for x in allq}
out["strategic_queries"]={t:m.get(t) for t in targets}
path=pathlib.Path("/home/maxdaguzan/regalospremium-dataset/reports/seo/gsc_position_compare_20261003.json")
path.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(out["ranges"],ensure_ascii=False,indent=2))
print("STRATEGIC")
for k,v in out["strategic_queries"].items(): print(k, json.dumps(v,ensure_ascii=False))
print("TOP_QUERIES")
for x in out["top_query"][:20]: print(json.dumps(x,ensure_ascii=False))
