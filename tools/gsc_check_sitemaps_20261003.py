import os,subprocess,json,urllib.request,urllib.parse
SITE="https://regalospremium.cl/"
G="/home/maxdaguzan/.local/gcloud-install/google-cloud-sdk/bin/gcloud"
ENV=dict(os.environ); ENV["CLOUDSDK_CONFIG"]="/home/maxdaguzan/.config/gcloud-rp-explorer"
SA="rp-google-ads-cli@able-marking-493221-m5.iam.gserviceaccount.com"
p=subprocess.run([G,"auth","print-access-token","--impersonate-service-account="+SA,"--scopes=https://www.googleapis.com/auth/webmasters","--quiet"],env=ENV,capture_output=True,text=True,timeout=60)
if p.returncode: raise SystemExit(p.stderr[-300:])
t=p.stdout.strip()
q=urllib.parse.quote(SITE,safe="")
req=urllib.request.Request(f"https://www.googleapis.com/webmasters/v3/sites/{q}/sitemaps",headers={"Authorization":"Bearer "+t})
with urllib.request.urlopen(req,timeout=30) as r: d=json.load(r)
for x in d.get("sitemap",[]):
 print(json.dumps({k:x.get(k) for k in ("path","lastSubmitted","lastDownloaded","isPending","warnings","errors")},ensure_ascii=False))
