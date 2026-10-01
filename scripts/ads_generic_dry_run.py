#!/usr/bin/env python3
"""Validate and render the generic Ads CSV plan. This script never calls Google Ads."""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
ADS_DIR = ROOT / "data" / "ads"
ALLOWED_MATCH_TYPES = {"EXACT", "PHRASE", "BROAD"}


def read_csv(path: Path, required: set[str]) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise ValueError(f"{path}: encabezados requeridos: {sorted(required)}")
        return [{key: (value or "").strip() for key, value in row.items()} for row in reader]


def validate_url(value: str, source: str) -> None:
    parsed = urlsplit(value)
    if parsed.scheme != "https" or parsed.netloc != "regalospremium.cl":
        raise ValueError(f"{source}: URL debe ser https://regalospremium.cl/...: {value}")


def build_plan(keywords: list[dict[str, str]], assets: list[dict[str, str]], targets: list[dict[str, str]]) -> dict:
    ready_keywords = [row for row in keywords if row["status"] == "READY"]
    ready_assets = [row for row in assets if row["status"] == "READY"]
    ready_targets = [row for row in targets if row["status"] == "READY"]
    if not ready_keywords or not ready_assets or not ready_targets:
        raise ValueError("Cada CSV debe contener al menos una fila READY")
    seen = set()
    for row in ready_keywords:
        if row["match_type"] not in ALLOWED_MATCH_TYPES or not row["keyword"] or not row["ad_group"]:
            raise ValueError(f"Keyword inválida: {row}")
        validate_url(row["final_url"], f"keyword {row['keyword']}")
        key = (row["keyword"].casefold(), row["match_type"], row["ad_group"])
        if key in seen: raise ValueError(f"Keyword duplicada: {key}")
        seen.add(key)
    counts = Counter(row["asset_type"] for row in ready_assets)
    if not (3 <= counts["HEADLINE"] <= 15 and 2 <= counts["DESCRIPTION"] <= 4):
        raise ValueError("RSA requiere 3-15 HEADLINE y 2-4 DESCRIPTION READY")
    for row in ready_assets:
        limit = 30 if row["asset_type"] == "HEADLINE" else 90 if row["asset_type"] == "DESCRIPTION" else 0
        if not limit or len(row["text"]) > limit or int(row["char_count"]) != len(row["text"]):
            raise ValueError(f"Asset RSA inválido: {row}")
    for row in ready_targets:
        if not row["label"]: raise ValueError(f"Target DSA sin label: {row}")
        validate_url(row["url"], f"DSA {row['label']}")
    return {
        "mode": "DRY_RUN_ONLY",
        "mutations_sent": 0,
        "precondition": "Ejecute ads_snapshot.py y revise el JSON antes de implementar cualquier mutación.",
        "pending_decisions": ["campaign_id o creación aprobada", "presupuesto y moneda", "estrategia de puja", "red/geografía/idioma", "confirmación final de URLs y exclusiones DSA"],
        "proposed": {
            "keywords": ready_keywords,
            "rsa": {"ad_group": ready_keywords[0]["ad_group"], "final_url": ready_keywords[0]["final_url"], "assets": ready_assets},
            "dsa_targets": ready_targets,
        },
    }


def parse_args():
    parser = argparse.ArgumentParser(description="Offline-only validation and plan for generic Ads assets")
    parser.add_argument("--keywords", type=Path, default=ADS_DIR / "ads_generic_keywords.csv")
    parser.add_argument("--rsa-assets", type=Path, default=ADS_DIR / "ads_rsa_generic_assets.csv")
    parser.add_argument("--dsa-targets", type=Path, default=ADS_DIR / "ads_dsa_targets.csv")
    parser.add_argument("--output", type=Path, default=ROOT / "reports" / "ads" / "generic-dry-run.json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    plan = build_plan(read_csv(args.keywords, {"keyword", "match_type", "ad_group", "final_url", "status"}),
                      read_csv(args.rsa_assets, {"asset_type", "text", "char_count", "status"}),
                      read_csv(args.dsa_targets, {"url", "label", "status"}))
    plan["generated_at"] = datetime.now(timezone.utc).isoformat()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"PASS: mode=DRY_RUN_ONLY mutations_sent=0 keywords={len(plan['proposed']['keywords'])} rsa_assets={len(plan['proposed']['rsa']['assets'])} dsa_targets={len(plan['proposed']['dsa_targets'])} output={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
