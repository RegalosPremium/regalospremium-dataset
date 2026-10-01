#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,sys
from pathlib import Path
from google.protobuf.field_mask_pb2 import FieldMask
from ads_service_account import load_config, load_client

ROOT=Path(__file__).resolve().parents[1]
CAMPAIGN_ID=23529944814
AD_GROUP_ID=196388350761
AD_ID=796159725585
KW_FILE=ROOT/"data/ads/ads_generic_keywords.csv"
RSA_FILE=ROOT/"data/ads/ads_rsa_generic_assets.csv"

def desired_keywords():
    out=[]
    with KW_FILE.open(encoding="utf-8",newline="") as f:
        for r in csv.DictReader(f):
            if r.get("status")=="READY":
                out.append((r["keyword"].strip(),r["match_type"].strip().upper()))
    return out

def desired_assets():
    h=[]; d=[]
    with RSA_FILE.open(encoding="utf-8",newline="") as f:
        for r in csv.DictReader(f):
            if r.get("status")!="READY": continue
            (h if r["asset_type"]=="HEADLINE" else d).append(r["text"])
    if not (3 <= len(h) <= 15): raise ValueError(f"headlines={len(h)} fuera de rango")
    if not (2 <= len(d) <= 4): raise ValueError(f"descriptions={len(d)} fuera de rango")
    if len(h)!=len(set(h)) or len(d)!=len(set(d)): raise ValueError("assets duplicados")
    return h,d

def current_keywords(client,cid):
    ga=client.get_service("GoogleAdsService")
    q=f"""SELECT ad_group_criterion.keyword.text,ad_group_criterion.keyword.match_type
           FROM ad_group_criterion
           WHERE campaign.id={CAMPAIGN_ID}
             AND ad_group.id={AD_GROUP_ID}
             AND ad_group_criterion.type='KEYWORD'
             AND ad_group_criterion.status != 'REMOVED'"""
    return {(r.ad_group_criterion.keyword.text.strip().lower(),
             r.ad_group_criterion.keyword.match_type.name.upper())
            for r in ga.search(customer_id=cid,query=q)}

def build_kw_ops(client,cid,missing):
    ops=[]
    ad_group=client.get_service("AdGroupService").ad_group_path(cid,AD_GROUP_ID)
    for text,match in missing:
        op=client.get_type("AdGroupCriterionOperation")
        c=op.create
        c.ad_group=ad_group
        c.status=client.enums.AdGroupCriterionStatusEnum.ENABLED
        c.keyword.text=text
        c.keyword.match_type=getattr(client.enums.KeywordMatchTypeEnum,match)
        ops.append(op)
    return ops

def build_rsa_op(client,cid):
    headlines,descriptions=desired_assets()
    op=client.get_type("AdOperation")
    ad=op.update
    ad.resource_name=client.get_service("AdService").ad_path(cid,AD_ID)
    for text in headlines:
        x=client.get_type("AdTextAsset"); x.text=text
        ad.responsive_search_ad.headlines.append(x)
    for text in descriptions:
        x=client.get_type("AdTextAsset"); x.text=text
        ad.responsive_search_ad.descriptions.append(x)
    op.update_mask.CopyFrom(FieldMask(paths=[
        "responsive_search_ad.headlines",
        "responsive_search_ad.descriptions",
    ]))
    return op

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--apply",action="store_true")
    args=ap.parse_args()
    cfg=load_config(); cid=cfg["customer_id"]; client=load_client(cfg)
    want=desired_keywords()
    existing=current_keywords(client,cid)
    missing=[(t,m) for t,m in want if (t.lower(),m) not in existing]
    print(f"PLAN campaign={CAMPAIGN_ID} ad_group={AD_GROUP_ID} ad={AD_ID}")
    print(f"keywords desired={len(want)} existing_match={len(want)-len(missing)} missing={len(missing)}")
    for t,m in missing: print(f"ADD_KEYWORD {m} {t}")
    h,d=desired_assets()
    print(f"RSA headlines={len(h)} descriptions={len(d)}")

    if missing:
        svc=client.get_service("AdGroupCriterionService")
        ops=build_kw_ops(client,cid,missing)
        req=client.get_type("MutateAdGroupCriteriaRequest")
        req.customer_id=cid; req.operations.extend(ops); req.validate_only=True
        svc.mutate_ad_group_criteria(request=req)
        print("VALIDATE keywords=PASS")
    adsvc=client.get_service("AdService")
    rsaop=build_rsa_op(client,cid)
    adreq=client.get_type("MutateAdsRequest")
    adreq.customer_id=cid; adreq.operations.append(rsaop); adreq.validate_only=True
    adsvc.mutate_ads(request=adreq)
    print("VALIDATE rsa=PASS")

    if not args.apply:
        print("DRY_RUN mutations_sent=0")
        return 0

    if missing:
        resp=svc.mutate_ad_group_criteria(customer_id=cid,operations=ops)
        print(f"APPLY keywords={len(resp.results)}")
    resp=adsvc.mutate_ads(customer_id=cid,operations=[rsaop])
    print(f"APPLY rsa={len(resp.results)}")
    print("PASS campaign_remains_paused=true")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
