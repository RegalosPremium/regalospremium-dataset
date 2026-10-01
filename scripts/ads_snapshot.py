#!/usr/bin/env python3
"""Create a JSON read-only backup of campaigns, ad groups, ads and keywords."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from ads_service_account import clean_customer_id, default_config_path, load_client, load_config, validate_key_file

ROOT = Path(__file__).resolve().parents[1]

QUERIES = {
    "campaigns": "SELECT campaign.id, campaign.name, campaign.status FROM campaign ORDER BY campaign.id",
    "ad_groups": "SELECT campaign.id, ad_group.id, ad_group.name, ad_group.status FROM ad_group ORDER BY ad_group.id",
    "ads": "SELECT campaign.id, ad_group.id, ad_group_ad.ad.id, ad_group_ad.status, ad_group_ad.ad.type, ad_group_ad.ad.final_urls FROM ad_group_ad WHERE ad_group_ad.status != 'REMOVED' ORDER BY ad_group_ad.ad.id",
    "keywords": "SELECT campaign.id, ad_group.id, ad_group_criterion.criterion_id, ad_group_criterion.status, ad_group_criterion.keyword.text, ad_group_criterion.keyword.match_type, ad_group_criterion.final_urls FROM ad_group_criterion WHERE ad_group_criterion.type = 'KEYWORD' AND ad_group_criterion.status != 'REMOVED' ORDER BY ad_group_criterion.criterion_id",
}


def parse_args():
    parser = argparse.ArgumentParser(description="Read-only Google Ads JSON snapshot")
    parser.add_argument("--config", type=Path, default=default_config_path())
    parser.add_argument("--customer-id", default=None)
    parser.add_argument("--output", type=Path, required=True, help="For example reports/ads/live/prewrite-YYYYMMDD.json")
    return parser.parse_args()


def _enum(value):
    return getattr(value, "name", str(value))


def collect(ga, customer_id: str) -> dict[str, list[dict]]:
    output: dict[str, list[dict]] = {key: [] for key in QUERIES}
    for kind, query in QUERIES.items():
        for row in ga.search(customer_id=customer_id, query=query):
            if kind == "campaigns": item = {"id": str(row.campaign.id), "name": row.campaign.name, "status": _enum(row.campaign.status)}
            elif kind == "ad_groups": item = {"campaign_id": str(row.campaign.id), "id": str(row.ad_group.id), "name": row.ad_group.name, "status": _enum(row.ad_group.status)}
            elif kind == "ads": item = {"campaign_id": str(row.campaign.id), "ad_group_id": str(row.ad_group.id), "id": str(row.ad_group_ad.ad.id), "status": _enum(row.ad_group_ad.status), "type": _enum(row.ad_group_ad.ad.type_), "final_urls": list(row.ad_group_ad.ad.final_urls)}
            else: item = {"campaign_id": str(row.campaign.id), "ad_group_id": str(row.ad_group.id), "criterion_id": str(row.ad_group_criterion.criterion_id), "status": _enum(row.ad_group_criterion.status), "text": row.ad_group_criterion.keyword.text, "match_type": _enum(row.ad_group_criterion.keyword.match_type), "final_urls": list(row.ad_group_criterion.final_urls)}
            output[kind].append(item)
    return output


def main() -> int:
    args = parse_args()
    config = load_config(args.config); customer_id = clean_customer_id(args.customer_id or config["customer_id"])
    validate_key_file(config)
    payload = {"generated_at": datetime.now(timezone.utc).isoformat(), "mode": "READ_ONLY_SNAPSHOT", "customer_id": customer_id}
    payload.update(collect(load_client(config).get_service("GoogleAdsService"), customer_id))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"PASS: snapshot={args.output} campaigns={len(payload['campaigns'])} ad_groups={len(payload['ad_groups'])} ads={len(payload['ads'])} keywords={len(payload['keywords'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
