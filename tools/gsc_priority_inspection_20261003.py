#!/usr/bin/env python3
import json, os, subprocess, urllib.request, urllib.error, urllib.parse, csv, pathlib, time
SITE="https://regalospremium.cl/"
GCLOUD="/home/maxdaguzan/.local/gcloud-install/google-cloud-sdk/bin/gcloud"
ENV=dict(os.environ); ENV["CLOUDSDK_CONFIG"]="/home/maxdaguzan/.config/gcloud-rp-explorer"
SA="rp-google-ads-cli@able-marking-493221-m5.iam.gserviceaccount.com"
SCOPE="https://www.googleapis.com/auth/webmasters.readonly"
p=subprocess.run([GCLOUD,"auth","print-access-token","--impersonate-service-account="+SA,"--scopes="+SCOPE,"--quiet"],env=ENV,capture_output=True,text=True,timeout=60)
if p.returncode or not p.stdout.strip():
    raise SystemExit("TOKEN_FAIL:"+((p.stderr or "")[-300:]))
token=p.stdout.strip()
headers={"Authorization":"Bearer "+token,"Content-Type":"application/json","User-Agent":"RP-GSC-Audit/2026-10-03"}
urls=[]
master="/home/maxdaguzan/regalospremium-dataset/data/gsc/coverage_drilldown_20261003_master.csv"
with open(master,encoding="utf-8-sig") as f:
    for r in csv.DictReader(f):
        if r["issue"]=="No se ha encontrado (404)" or r["issue"].startswith("Duplicada: Google") or "noindex" in r["issue"].lower():
            urls.append((r["issue"],r["url"]))
out=[]
for issue,url in urls:
    row={"issue":issue,"url":url}
    body=json.dumps({"inspectionUrl":url,"siteUrl":SITE,"languageCode":"es-CL"}).encode()
    req=urllib.request.Request("https://searchconsole.googleapis.com/v1/urlInspection/index:inspect",data=body,headers=headers,method="POST")
    try:
        with urllib.request.urlopen(req,timeout=40) as resp:
            d=json.load(resp)
        ir=d.get("inspectionResult",{}).get("indexStatusResult",{})
        row.update({
            "inspection_verdict":ir.get("verdict"),
            "coverageState":ir.get("coverageState"),
            "robotsTxtState":ir.get("robotsTxtState"),
            "indexingState":ir.get("indexingState"),
            "lastCrawlTime":ir.get("lastCrawlTime"),
            "pageFetchState":ir.get("pageFetchState"),
            "googleCanonical":ir.get("googleCanonical"),
            "userCanonical":ir.get("userCanonical"),
            "referringUrls":ir.get("referringUrls",[])[:10],
        })
    except urllib.error.HTTPError as e:
        b=e.read().decode("utf-8","replace")
        row["inspection_error"]=f"HTTP {e.code}: {b[:500]}"
    except Exception as e:
        row["inspection_error"]=repr(e)
    # Search Analytics last 90 settled days, exact page
    sa_body=json.dumps({
        "startDate":"2026-07-01","endDate":"2026-09-30",
        "dimensions":["page"],"rowLimit":10,
        "dimensionFilterGroups":[{"filters":[{"dimension":"page","operator":"equals","expression":url}]}]
    }).encode()
    siteq=urllib.parse.quote(SITE,safe="")
    req2=urllib.request.Request(f"https://www.googleapis.com/webmasters/v3/sites/{siteq}/searchAnalytics/query",data=sa_body,headers=headers,method="POST")
    try:
        with urllib.request.urlopen(req2,timeout=40) as resp:
            d2=json.load(resp)
        rows=d2.get("rows",[])
        row["sa_clicks"]=sum(x.get("clicks",0) for x in rows)
        row["sa_impressions"]=sum(x.get("impressions",0) for x in rows)
        row["sa_rows"]=len(rows)
    except urllib.error.HTTPError as e:
        b=e.read().decode("utf-8","replace")
        row["sa_error"]=f"HTTP {e.code}: {b[:500]}"
    except Exception as e:
        row["sa_error"]=repr(e)
    out.append(row)
    print(json.dumps(row,ensure_ascii=False),flush=True)
path="/home/maxdaguzan/regalospremium-dataset/reports/seo/gsc_priority_inspection_20261003.json"
pathlib.Path(path).write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("WROTE",path,"COUNT",len(out))
