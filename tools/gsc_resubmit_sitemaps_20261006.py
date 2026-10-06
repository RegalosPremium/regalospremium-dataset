#!/usr/bin/env python3
import json, os, subprocess, urllib.request, urllib.error, urllib.parse, pathlib, datetime
SITE="https://regalospremium.cl/"
GCLOUD="/home/maxdaguzan/.local/gcloud-install/google-cloud-sdk/bin/gcloud"
CFG="/home/maxdaguzan/.config/gcloud-rp-explorer"
SA="rp-google-ads-cli@able-marking-493221-m5.iam.gserviceaccount.com"
SCOPE="https://www.googleapis.com/auth/webmasters"
OUT=pathlib.Path("/home/maxdaguzan/regalospremium-riskfix/reports/seo/gsc_sitemap_resubmit_20261006.json")
env=dict(os.environ); env["CLOUDSDK_CONFIG"]=CFG
p=subprocess.run([GCLOUD,"auth","print-access-token","--impersonate-service-account="+SA,"--scopes="+SCOPE,"--quiet"],env=env,capture_output=True,text=True,timeout=60)
if p.returncode or not p.stdout.strip():
    raise SystemExit("TOKEN_FAIL:"+(p.stderr[-500:] if p.stderr else "empty"))
token=p.stdout.strip()
headers={"Authorization":"Bearer "+token,"Content-Type":"application/json","User-Agent":"RP-GSC-Maintenance/2026-10-06"}

def get_json(url):
    req=urllib.request.Request(url,headers=headers)
    with urllib.request.urlopen(req,timeout=40) as r:
        return r.status,json.load(r)

def put_empty(url):
    req=urllib.request.Request(url,data=b"",headers=headers,method="PUT")
    try:
        with urllib.request.urlopen(req,timeout=40) as r:
            body=r.read()
            return r.status,body.decode("utf-8","replace")
    except urllib.error.HTTPError as e:
        return e.code,e.read().decode("utf-8","replace")

siteq=urllib.parse.quote(SITE,safe="")
status,sites=get_json("https://www.googleapis.com/webmasters/v3/sites")
entry=next((x for x in sites.get("siteEntry",[]) if x.get("siteUrl")==SITE),None)
if not entry:
    raise SystemExit("SITE_NOT_FOUND")
before_status,before=get_json(f"https://www.googleapis.com/webmasters/v3/sites/{siteq}/sitemaps")
paths=[x.get("path") for x in before.get("sitemap",[]) if x.get("path")]
results=[]
for sitemap in paths:
    feedq=urllib.parse.quote(sitemap,safe="")
    st,body=put_empty(f"https://www.googleapis.com/webmasters/v3/sites/{siteq}/sitemaps/{feedq}")
    results.append({"sitemap":sitemap,"http_status":st,"body":body[:500]})
after_status,after=get_json(f"https://www.googleapis.com/webmasters/v3/sites/{siteq}/sitemaps")
report={
    "time_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "site":entry,
    "before_http":before_status,
    "before":before.get("sitemap",[]),
    "submitted":results,
    "after_http":after_status,
    "after":after.get("sitemap",[]),
}
OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps({"site":entry,"submitted":results,"after":[{"path":x.get("path"),"lastSubmitted":x.get("lastSubmitted"),"warnings":x.get("warnings"),"errors":x.get("errors"),"isPending":x.get("isPending")} for x in after.get("sitemap",[])]},ensure_ascii=False))
