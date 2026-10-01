#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv
from pathlib import Path
from google.protobuf.field_mask_pb2 import FieldMask
from ads_service_account import load_config,load_client

ROOT=Path(__file__).resolve().parents[1]
CAMPAIGN_ID=23529944814
GROUP_NAME="DSA | Canonicales B2B"
CPC_MICROS=100_000_000
TARGETS=ROOT/"data/ads/ads_dsa_targets.csv"

def targets():
    out=[]
    with TARGETS.open(encoding="utf-8",newline="") as f:
        for r in csv.DictReader(f):
            if r.get("status")!="READY": continue
            url=r["url"].strip()
            if url=="https://regalospremium.cl/":
                continue
            out.append((url,r["label"].strip()))
    return out

def validate_campaign_setting(client,cid):
    op=client.get_type("CampaignOperation")
    c=op.update
    c.resource_name=client.get_service("CampaignService").campaign_path(cid,CAMPAIGN_ID)
    c.dynamic_search_ads_setting.domain_name="regalospremium.cl"
    c.dynamic_search_ads_setting.language_code="es"
    c.dynamic_search_ads_setting.use_supplied_urls_only=False
    op.update_mask.CopyFrom(FieldMask(paths=[
        "dynamic_search_ads_setting.domain_name",
        "dynamic_search_ads_setting.language_code",
        "dynamic_search_ads_setting.use_supplied_urls_only",
    ]))
    req=client.get_type("MutateCampaignsRequest")
    req.customer_id=cid; req.operations.append(op); req.validate_only=True
    client.get_service("CampaignService").mutate_campaigns(request=req)
    return op

def existing_group(client,cid):
    ga=client.get_service("GoogleAdsService")
    q=f"""SELECT ad_group.id,ad_group.name,ad_group.status,ad_group.type
           FROM ad_group
           WHERE campaign.id={CAMPAIGN_ID}
             AND ad_group.name='{GROUP_NAME}'"""
    rows=list(ga.search(customer_id=cid,query=q))
    return rows[0] if rows else None

def build_group_op(client,cid):
    op=client.get_type("AdGroupOperation")
    g=op.create
    g.name=GROUP_NAME
    g.campaign=client.get_service("CampaignService").campaign_path(cid,CAMPAIGN_ID)
    g.status=client.enums.AdGroupStatusEnum.PAUSED
    g.type_=client.enums.AdGroupTypeEnum.SEARCH_DYNAMIC_ADS
    g.cpc_bid_micros=CPC_MICROS
    return op

def validate_group(client,cid,op):
    req=client.get_type("MutateAdGroupsRequest")
    req.customer_id=cid; req.operations.append(op); req.validate_only=True
    client.get_service("AdGroupService").mutate_ad_groups(request=req)

def build_ad_op(client,group_rn):
    op=client.get_type("AdGroupAdOperation")
    x=op.create
    x.ad_group=group_rn
    x.status=client.enums.AdGroupAdStatusEnum.PAUSED
    x.ad.expanded_dynamic_search_ad.description="Regalos corporativos y merchandising para empresas. Cotiza por volumen."
    x.ad.expanded_dynamic_search_ad.description2="Productos con logo y despacho a todo Chile. Atención B2B."
    return op

def build_criteria_ops(client,group_rn):
    ops=[]
    for url,label in targets():
        op=client.get_type("AdGroupCriterionOperation")
        c=op.create
        c.ad_group=group_rn
        c.status=client.enums.AdGroupCriterionStatusEnum.ENABLED
        c.webpage.criterion_name=label
        cond=client.get_type("WebpageConditionInfo")
        cond.operand=client.enums.WebpageConditionOperandEnum.URL
        cond.argument=url
        c.webpage.conditions.append(cond)
        ops.append(op)
    return ops

def validate_ad_and_criteria(client,cid,group_rn):
    adreq=client.get_type("MutateAdGroupAdsRequest")
    adreq.customer_id=cid; adreq.operations.append(build_ad_op(client,group_rn)); adreq.validate_only=True
    client.get_service("AdGroupAdService").mutate_ad_group_ads(request=adreq)
    creq=client.get_type("MutateAdGroupCriteriaRequest")
    creq.customer_id=cid; creq.operations.extend(build_criteria_ops(client,group_rn)); creq.validate_only=True
    client.get_service("AdGroupCriterionService").mutate_ad_group_criteria(request=creq)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--apply",action="store_true")
    args=ap.parse_args()
    cfg=load_config(); cid=cfg["customer_id"]; client=load_client(cfg)
    ts=targets()
    print(f"PLAN campaign={CAMPAIGN_ID} group={GROUP_NAME!r} targets={len(ts)}")
    for u,l in ts: print(f"TARGET {l} {u}")

    camp_op=validate_campaign_setting(client,cid)
    print("VALIDATE campaign_dsa_setting=PASS")

    row=existing_group(client,cid)
    if row:
        group_rn=client.get_service("AdGroupService").ad_group_path(cid,row.ad_group.id)
        print(f"EXISTING_GROUP id={row.ad_group.id} status={row.ad_group.status.name} type={row.ad_group.type_.name}")
        if not args.apply:
            validate_ad_and_criteria(client,cid,group_rn)
            print("VALIDATE ad_and_targets=PASS")
            print("DRY_RUN mutations_sent=0")
            return 0
    else:
        if not args.apply:
            print("DRY_RUN campaign_setting_validated=true; dsa_group_validation_requires_persisted_setting; mutations_sent=0")
            return 0

    # Apply campaign DSA settings. Campaign remains paused.
    cresp=client.get_service("CampaignService").mutate_campaigns(customer_id=cid,operations=[camp_op])
    print(f"APPLY campaign_dsa_setting={len(cresp.results)}")

    row=existing_group(client,cid)
    if row:
        group_rn=client.get_service("AdGroupService").ad_group_path(cid,row.ad_group.id)
    else:
        gop=build_group_op(client,cid)
        validate_group(client,cid,gop)
        print("VALIDATE dsa_group=PASS")
        gresp=client.get_service("AdGroupService").mutate_ad_groups(
            customer_id=cid,operations=[gop])
        group_rn=gresp.results[0].resource_name
        print(f"APPLY dsa_group={group_rn}")

    validate_ad_and_criteria(client,cid,group_rn)
    print("VALIDATE ad_and_targets=PASS")

    # Avoid duplicate DSA ad/criteria if rerun.
    ga=client.get_service("GoogleAdsService")
    gid=group_rn.rsplit("/",1)[-1]
    adq=f"""SELECT ad_group_ad.ad.id FROM ad_group_ad
            WHERE ad_group.id={gid}
              AND ad_group_ad.ad.type='EXPANDED_DYNAMIC_SEARCH_AD'
              AND ad_group_ad.status != 'REMOVED'"""
    ads=list(ga.search(customer_id=cid,query=adq))
    if not ads:
        aresp=client.get_service("AdGroupAdService").mutate_ad_group_ads(
            customer_id=cid,operations=[build_ad_op(client,group_rn)])
        print(f"APPLY dsa_ad={len(aresp.results)}")
    else:
        print(f"SKIP dsa_ad existing={len(ads)}")

    cq=f"""SELECT ad_group_criterion.criterion_id,ad_group_criterion.webpage.criterion_name
           FROM ad_group_criterion
           WHERE ad_group.id={gid}
             AND ad_group_criterion.type='WEBPAGE'
             AND ad_group_criterion.status != 'REMOVED'"""
    existing={r.ad_group_criterion.webpage.criterion_name for r in ga.search(customer_id=cid,query=cq)}
    missing=[]
    for op in build_criteria_ops(client,group_rn):
        if op.create.webpage.criterion_name not in existing:
            missing.append(op)
    if missing:
        r=client.get_service("AdGroupCriterionService").mutate_ad_group_criteria(
            customer_id=cid,operations=missing)
        print(f"APPLY webpage_targets={len(r.results)}")
    else:
        print("SKIP webpage_targets existing_all=true")
    print("PASS dsa_group_paused=true campaign_paused=true")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
