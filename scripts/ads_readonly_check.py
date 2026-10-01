#!/usr/bin/env python3
"""Read-only Google Ads access validation for the configured service account."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ads_service_account import clean_customer_id, default_config_path, load_client, load_config, validate_auth


def parse_args():
    parser = argparse.ArgumentParser(description="Validate service-account access without any Google Ads mutation")
    parser.add_argument("--config", type=Path, default=default_config_path())
    parser.add_argument("--customer-id", default=None, help="Defaults to customer_id in private config")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        config = load_config(args.config)
        customer_id = clean_customer_id(args.customer_id or config["customer_id"])
        auth_info = validate_auth(config)
        client = load_client(config)
        accessible = client.get_service("CustomerService").list_accessible_customers()
        ga = client.get_service("GoogleAdsService")
        query = """
          SELECT campaign.id, campaign.name, campaign.status
          FROM campaign
          WHERE campaign.status != 'REMOVED'
          ORDER BY campaign.id
        """
        campaigns = []
        for row in ga.search(customer_id=customer_id, query=query):
            campaigns.append({"id": str(row.campaign.id), "name": row.campaign.name,
                              "status": row.campaign.status.name})
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print(f"PASS: local auth validated mode={auth_info['auth_mode']}")
    print(f"service_account={auth_info['service_account_email']}")
    print(f"accessible_customers={len(accessible.resource_names)}")
    print(f"customer_id={customer_id} active_campaigns={len(campaigns)}")
    for campaign in campaigns:
        print(f"campaign={campaign['id']} status={campaign['status']} name={campaign['name']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
