import json,os,subprocess,urllib.request,urllib.parse,pathlib
SITE="https://regalospremium.cl/"
URLS=["https://regalospremium.cl/roller-pen-titan.html","https://regalospremium.cl/boligrafos-metalicos-y-ejecutivos/boligrafo-duero.html"]
G="/home/maxdaguzan/.local/gcloud-install/google-cloud-sdk/bin/gcloud"
ENV=dict(os.environ); ENV["CLOUDSDK_CONFIG"]="/home/maxdaguzan/.config/gcloud-rp-explorer"
SA="rp-google-ads-cli@able-marking-493221-m5.iam.gserviceaccount.com"
p=subprocess.run([G,"auth","print-access-token","--impersonate-service-account="+SA,"--scopes=https://www.googleapis.com/auth/webmasters.readonly","--quiet"],env=ENV,capture_output=True,text=True,timeout=60)
if p.returncode: raise SystemExit(p.stderr[-500:])
tok=p.stdout.strip(); h={"Authorization":"Bearer "+tok,"Content-Type":"application/json"}
out=[]
for u in URLS:
    body=json.dumps({"inspectionUrl":u,"siteUrl":SITE,"languageCode":"es-CL"}).encode()
    req=urllib.request.Request("https://searchconsole.googleapis.com/v1/urlInspection/index:inspect",data=body,headers=h,method="POST")
    with urllib.request.urlopen(req,timeout=40) as r: d=json.load(r)
    ir=d.get("inspectionResult",{}).get("indexStatusResult",{})
    row={"url":u,**{k:ir.get(k) for k in ["verdict","coverageState","robotsTxtState","indexingState","lastCrawlTime","pageFetchState","googleCanonical","userCanonical"]}}
    sa=json.dumps({"startDate":"2026-07-01","endDate":"2026-09-30","dimensions":["page"],"rowLimit":10,"dimensionFilterGroups":[{"filters":[{"dimension":"page","operator":"equals","expression":u}]}]}).encode()
    siteq=urllib.parse.quote(SITE,safe="")
    req2=urllib.request.Request(f"https://www.googleapis.com/webmasters/v3/sites/{siteq}/searchAnalytics/query",data=sa,headers=h,method="POST")
    with urllib.request.urlopen(req2,timeout=40) as r: d2=json.load(r)
    rows=d2.get("rows",[]); row["clicks"]=sum(x.get("clicks",0) for x in rows); row["impressions"]=sum(x.get("impressions",0) for x in rows)
    out.append(row); print(json.dumps(row,ensure_ascii=False))
pathlib.Path("/home/maxdaguzan/regalospremium-dataset/reports/seo/gsc_5xx_inspection_20261003.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
