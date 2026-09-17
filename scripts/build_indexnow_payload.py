#!/usr/bin/env python3
import argparse, json, os, sys
from urllib.parse import urlparse
p=argparse.ArgumentParser(description="Build an IndexNow JSON payload from changed URLs only.")
p.add_argument("url_file", help="Text file with one new/changed/deleted URL per line")
p.add_argument("--key", default=os.getenv("INDEXNOW_KEY"))
p.add_argument("--key-location", default=os.getenv("INDEXNOW_KEY_LOCATION"))
a=p.parse_args()
urls=[x.strip() for x in open(a.url_file,encoding="utf-8") if x.strip() and not x.lstrip().startswith("#")]
if not urls: sys.exit("No changed URLs supplied")
if len(urls)>10000: sys.exit("IndexNow permits at most 10,000 URLs per payload")
hosts={urlparse(u).netloc for u in urls}
if hosts!={"regalospremium.cl"}: sys.exit(f"Unexpected hosts: {sorted(hosts)}")
if not a.key: sys.exit("Set INDEXNOW_KEY or use --key")
payload={"host":"regalospremium.cl","key":a.key,"urlList":urls}
if a.key_location: payload["keyLocation"]=a.key_location
print(json.dumps(payload,ensure_ascii=False,indent=2))
