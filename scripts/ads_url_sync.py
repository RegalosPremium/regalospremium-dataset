#!/usr/bin/env python3
"""Synchronize catalog URL changes from GitHub into Google Ads.

Dry-run is the default. Mutations require --apply.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from dataclasses import asdict, dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CHANGES = ROOT / "data" / "url_changes.csv"
DEFAULT_CONFIG = ROOT / "config" / "google-ads.yaml"
ALLOWED_HOST = "regalospremium.cl"
READY = "READY"


@dataclass(frozen=True)
class UrlChange:
    change_id: str
    product_id: str
    old_url: str
    new_url: str
    effective_date: str
    status: str
    notes: str = ""


@dataclass
class Reference:
    kind: str
    resource_name: str
    label: str
    final_urls: list[str]
    final_mobile_urls: list[str]
    metadata: dict[str, Any]


def clean_customer_id(value: str) -> str:
    return value.replace("-", "").strip()


def _parts(url: str):
    return urlsplit(url.strip())


def validate_change(change: UrlChange) -> None:
    if not change.change_id:
        raise ValueError("change_id vacío")
    old, new = _parts(change.old_url), _parts(change.new_url)
    if old.scheme != "https" or new.scheme != "https":
        raise ValueError(f"{change.change_id}: sólo se permiten URLs https")
    if old.netloc != ALLOWED_HOST or new.netloc != ALLOWED_HOST:
        raise ValueError(f"{change.change_id}: host debe ser {ALLOWED_HOST}")
    if change.old_url == change.new_url:
        raise ValueError(f"{change.change_id}: old_url y new_url son iguales")


def replace_url(value: str, old_url: str, new_url: str) -> tuple[str, bool]:
    """Replace the catalog URL while preserving Ads query/fragment parameters."""
    current, old, new = _parts(value), _parts(old_url), _parts(new_url)
    if (current.scheme, current.netloc, current.path) != (old.scheme, old.netloc, old.path):
        return value, False
    if old.query and current.query != old.query:
        return value, False
    query = new.query or current.query
    fragment = new.fragment or current.fragment
    return urlunsplit((new.scheme, new.netloc, new.path, query, fragment)), True


def replace_list(values: Iterable[str], old_url: str, new_url: str) -> tuple[list[str], bool]:
    output, changed = [], False
    for value in values:
        updated, hit = replace_url(value, old_url, new_url)
        output.append(updated)
        changed = changed or hit
    return output, changed


def load_changes(path: Path, change_id: str | None = None, include_future: bool = False) -> list[UrlChange]:
    with path.open(encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))
    changes = [UrlChange(**{k: (row.get(k) or "").strip() for k in UrlChange.__dataclass_fields__}) for row in rows]
    selected: list[UrlChange] = []
    today = date.today().isoformat()
    for change in changes:
        validate_change(change)
        if change_id and change.change_id != change_id:
            continue
        if not change_id and change.status != READY:
            continue
        if change.effective_date and change.effective_date > today and not include_future:
            continue
        selected.append(change)
    return selected


def enum_name(value: Any) -> str:
    return getattr(value, "name", str(value))


class AdsSynchronizer:
    def __init__(self, client: Any, customer_id: str):
        self.client = client
        self.customer_id = clean_customer_id(customer_id)
        self.ga = client.get_service("GoogleAdsService", version="v25")

    def rows(self, query: str):
        for batch in self.ga.search_stream(customer_id=self.customer_id, query=query):
            yield from batch.results

    def inventory(self, change: UrlChange) -> list[Reference]:
        refs: list[Reference] = []
        refs.extend(self._ads(change))
        refs.extend(self._keywords(change))
        refs.extend(self._asset_groups(change))
        refs.extend(self._assets(change))
        return refs

    @staticmethod
    def _matches(urls: Iterable[str], change: UrlChange) -> bool:
        return any(replace_url(u, change.old_url, change.new_url)[1] for u in urls)

    def _ads(self, change: UrlChange) -> list[Reference]:
        query = """
          SELECT campaign.id, campaign.name, ad_group.id, ad_group.name,
                 ad_group_ad.resource_name, ad_group_ad.status,
                 ad_group_ad.ad.id, ad_group_ad.ad.resource_name,
                 ad_group_ad.ad.type, ad_group_ad.ad.final_urls,
                 ad_group_ad.ad.final_mobile_urls
          FROM ad_group_ad
          WHERE ad_group_ad.status != 'REMOVED'
        """
        out = []
        for row in self.rows(query):
            urls = list(row.ad_group_ad.ad.final_urls)
            mobile = list(row.ad_group_ad.ad.final_mobile_urls)
            if not (self._matches(urls, change) or self._matches(mobile, change)):
                continue
            out.append(Reference(
                "AD", row.ad_group_ad.ad.resource_name,
                f"{row.campaign.name} / {row.ad_group.name} / ad {row.ad_group_ad.ad.id}",
                urls, mobile,
                {"campaign_id": str(row.campaign.id), "ad_group_id": str(row.ad_group.id),
                 "ad_type": enum_name(row.ad_group_ad.ad.type_)},
            ))
        return out

    def _keywords(self, change: UrlChange) -> list[Reference]:
        query = """
          SELECT campaign.id, campaign.name, ad_group.id, ad_group.name,
                 ad_group_criterion.resource_name, ad_group_criterion.criterion_id,
                 ad_group_criterion.status, ad_group_criterion.keyword.text,
                 ad_group_criterion.final_urls, ad_group_criterion.final_mobile_urls
          FROM ad_group_criterion
          WHERE ad_group_criterion.status != 'REMOVED'
            AND ad_group_criterion.type = 'KEYWORD'
        """
        out = []
        for row in self.rows(query):
            urls = list(row.ad_group_criterion.final_urls)
            mobile = list(row.ad_group_criterion.final_mobile_urls)
            if not (self._matches(urls, change) or self._matches(mobile, change)):
                continue
            out.append(Reference(
                "KEYWORD", row.ad_group_criterion.resource_name,
                f"{row.campaign.name} / {row.ad_group.name} / {row.ad_group_criterion.keyword.text}",
                urls, mobile,
                {"campaign_id": str(row.campaign.id), "ad_group_id": str(row.ad_group.id),
                 "criterion_id": str(row.ad_group_criterion.criterion_id)},
            ))
        return out

    def _asset_groups(self, change: UrlChange) -> list[Reference]:
        query = """
          SELECT campaign.id, campaign.name, asset_group.id, asset_group.name,
                 asset_group.resource_name, asset_group.status,
                 asset_group.final_urls, asset_group.final_mobile_urls
          FROM asset_group
          WHERE asset_group.status != 'REMOVED'
        """
        out = []
        for row in self.rows(query):
            urls = list(row.asset_group.final_urls)
            mobile = list(row.asset_group.final_mobile_urls)
            if not (self._matches(urls, change) or self._matches(mobile, change)):
                continue
            out.append(Reference(
                "ASSET_GROUP", row.asset_group.resource_name,
                f"{row.campaign.name} / {row.asset_group.name}", urls, mobile,
                {"campaign_id": str(row.campaign.id), "asset_group_id": str(row.asset_group.id)},
            ))
        return out

    def _assets(self, change: UrlChange) -> list[Reference]:
        query = """
          SELECT asset.resource_name, asset.id, asset.name, asset.type, asset.source,
                 asset.final_urls, asset.final_mobile_urls, asset.tracking_url_template,
                 asset.final_url_suffix, asset.url_custom_parameters,
                 asset.sitelink_asset.link_text, asset.sitelink_asset.description1,
                 asset.sitelink_asset.description2, asset.sitelink_asset.start_date,
                 asset.sitelink_asset.end_date, asset.sitelink_asset.ad_schedule_targets
          FROM asset
          WHERE asset.source = 'ADVERTISER'
        """
        out = []
        for row in self.rows(query):
            urls = list(row.asset.final_urls)
            mobile = list(row.asset.final_mobile_urls)
            if not (self._matches(urls, change) or self._matches(mobile, change)):
                continue
            schedules = []
            for s in row.asset.sitelink_asset.ad_schedule_targets:
                schedules.append({
                    "day_of_week": int(s.day_of_week), "start_hour": int(s.start_hour),
                    "start_minute": int(s.start_minute), "end_hour": int(s.end_hour),
                    "end_minute": int(s.end_minute),
                })
            custom = [{"key": p.key, "value": p.value} for p in row.asset.url_custom_parameters]
            out.append(Reference(
                "ASSET", row.asset.resource_name,
                f"asset {row.asset.id} {row.asset.name or ''}".strip(), urls, mobile,
                {"asset_id": str(row.asset.id), "asset_type": enum_name(row.asset.type_),
                 "source": enum_name(row.asset.source), "tracking_url_template": row.asset.tracking_url_template,
                 "final_url_suffix": row.asset.final_url_suffix,
                 "sitelink": {"link_text": row.asset.sitelink_asset.link_text,
                              "description1": row.asset.sitelink_asset.description1,
                              "description2": row.asset.sitelink_asset.description2,
                              "start_date": row.asset.sitelink_asset.start_date,
                              "end_date": row.asset.sitelink_asset.end_date,
                              "schedules": schedules}, "custom_parameters": custom},
            ))
        return out

    def apply_reference(self, ref: Reference, change: UrlChange) -> dict[str, Any]:
        if ref.kind == "AD":
            return self._update_ad(ref, change)
        if ref.kind == "KEYWORD":
            return self._update_keyword(ref, change)
        if ref.kind == "ASSET_GROUP":
            return self._update_asset_group(ref, change)
        if ref.kind == "ASSET":
            if ref.metadata.get("asset_type") != "SITELINK":
                raise RuntimeError(f"Asset URL no soportado automáticamente: {ref.metadata.get('asset_type')}")
            return self._replace_sitelink(ref, change)
        raise RuntimeError(f"Tipo de referencia desconocido: {ref.kind}")

    def _new_urls(self, ref: Reference, change: UrlChange):
        urls, hit1 = replace_list(ref.final_urls, change.old_url, change.new_url)
        mobile, hit2 = replace_list(ref.final_mobile_urls, change.old_url, change.new_url)
        return urls, mobile, hit1, hit2

    def _update_ad(self, ref: Reference, change: UrlChange) -> dict[str, Any]:
        urls, mobile, hit1, hit2 = self._new_urls(ref, change)
        op = self.client.get_type("AdOperation", version="v25")
        op.update.resource_name = ref.resource_name
        if hit1:
            op.update.final_urls.extend(urls); op.update_mask.paths.append("final_urls")
        if hit2:
            op.update.final_mobile_urls.extend(mobile); op.update_mask.paths.append("final_mobile_urls")
        svc = self.client.get_service("AdService", version="v25")
        result = svc.mutate_ads(customer_id=self.customer_id, operations=[op])
        return {"resource_name": result.results[0].resource_name, "action": "UPDATED_AD"}

    def _update_keyword(self, ref: Reference, change: UrlChange) -> dict[str, Any]:
        urls, mobile, hit1, hit2 = self._new_urls(ref, change)
        op = self.client.get_type("AdGroupCriterionOperation", version="v25")
        op.update.resource_name = ref.resource_name
        if hit1:
            op.update.final_urls.extend(urls); op.update_mask.paths.append("final_urls")
        if hit2:
            op.update.final_mobile_urls.extend(mobile); op.update_mask.paths.append("final_mobile_urls")
        svc = self.client.get_service("AdGroupCriterionService", version="v25")
        result = svc.mutate_ad_group_criteria(customer_id=self.customer_id, operations=[op])
        return {"resource_name": result.results[0].resource_name, "action": "UPDATED_KEYWORD"}

    def _update_asset_group(self, ref: Reference, change: UrlChange) -> dict[str, Any]:
        urls, mobile, hit1, hit2 = self._new_urls(ref, change)
        op = self.client.get_type("AssetGroupOperation", version="v25")
        op.update.resource_name = ref.resource_name
        if hit1:
            op.update.final_urls.extend(urls); op.update_mask.paths.append("final_urls")
        if hit2:
            op.update.final_mobile_urls.extend(mobile); op.update_mask.paths.append("final_mobile_urls")
        svc = self.client.get_service("AssetGroupService", version="v25")
        result = svc.mutate_asset_groups(customer_id=self.customer_id, operations=[op])
        return {"resource_name": result.results[0].resource_name, "action": "UPDATED_ASSET_GROUP"}

    def _asset_links(self, asset_rn: str) -> list[dict[str, Any]]:
        escaped = asset_rn.replace("'", "\\'")
        specs = [
            ("CAMPAIGN_ASSET", "campaign_asset", "campaign_asset.resource_name, campaign_asset.campaign, campaign_asset.asset, campaign_asset.field_type, campaign_asset.status"),
            ("AD_GROUP_ASSET", "ad_group_asset", "ad_group_asset.resource_name, ad_group_asset.ad_group, ad_group_asset.asset, ad_group_asset.field_type, ad_group_asset.status"),
            ("CUSTOMER_ASSET", "customer_asset", "customer_asset.resource_name, customer_asset.asset, customer_asset.field_type, customer_asset.status"),
        ]
        links = []
        for kind, resource, fields in specs:
            query = f"SELECT {fields} FROM {resource} WHERE {resource}.asset = '{escaped}' AND {resource}.status != 'REMOVED'"
            for row in self.rows(query):
                obj = getattr(row, resource)
                parent_field = {"campaign_asset": "campaign", "ad_group_asset": "ad_group", "customer_asset": None}[resource]
                links.append({"kind": kind, "resource_name": obj.resource_name,
                              "parent": (getattr(obj, parent_field) if parent_field else None), "status": int(obj.status),
                              "field_type": int(obj.field_type)})
        return links

    def _replace_sitelink(self, ref: Reference, change: UrlChange) -> dict[str, Any]:
        links = self._asset_links(ref.resource_name)
        if not links:
            raise RuntimeError(f"Sitelink sin vínculos activos: {ref.resource_name}")
        urls, mobile, _, _ = self._new_urls(ref, change)
        op = self.client.get_type("AssetOperation", version="v25")
        asset = op.create
        asset.final_urls.extend(urls); asset.final_mobile_urls.extend(mobile)
        meta = ref.metadata
        if meta.get("tracking_url_template"): asset.tracking_url_template = meta["tracking_url_template"]
        if meta.get("final_url_suffix"): asset.final_url_suffix = meta["final_url_suffix"]
        for item in meta.get("custom_parameters", []):
            cp = self.client.get_type("CustomParameter", version="v25"); cp.key = item["key"]; cp.value = item["value"]
            asset.url_custom_parameters.append(cp)
        slm = meta["sitelink"]; sl = asset.sitelink_asset
        sl.link_text = slm["link_text"]
        if slm.get("description1"): sl.description1 = slm["description1"]
        if slm.get("description2"): sl.description2 = slm["description2"]
        if slm.get("start_date"): sl.start_date = slm["start_date"]
        if slm.get("end_date"): sl.end_date = slm["end_date"]
        for item in slm.get("schedules", []):
            sched = self.client.get_type("AdScheduleInfo", version="v25")
            for key, value in item.items(): setattr(sched, key, value)
            sl.ad_schedule_targets.append(sched)
        asset_svc = self.client.get_service("AssetService", version="v25")
        created = asset_svc.mutate_assets(customer_id=self.customer_id, operations=[op]).results[0].resource_name

        created_links = []
        for link in links:
            if link["kind"] == "CAMPAIGN_ASSET":
                typ, svc_name, method, parent = "CampaignAssetOperation", "CampaignAssetService", "mutate_campaign_assets", "campaign"
            elif link["kind"] == "AD_GROUP_ASSET":
                typ, svc_name, method, parent = "AdGroupAssetOperation", "AdGroupAssetService", "mutate_ad_group_assets", "ad_group"
            else:
                typ, svc_name, method, parent = "CustomerAssetOperation", "CustomerAssetService", "mutate_customer_assets", None
            create_op = self.client.get_type(typ, version="v25")
            obj = create_op.create

            if parent: setattr(obj, parent, link["parent"])
            obj.asset = created
            obj.field_type = link["field_type"]; obj.status = link["status"]
            svc = self.client.get_service(svc_name, version="v25")
            response = getattr(svc, method)(customer_id=self.customer_id, operations=[create_op])
            created_links.append(response.results[0].resource_name)

        for link in links:
            if link["kind"] == "CAMPAIGN_ASSET": typ, svc_name, method = "CampaignAssetOperation", "CampaignAssetService", "mutate_campaign_assets"
            elif link["kind"] == "AD_GROUP_ASSET": typ, svc_name, method = "AdGroupAssetOperation", "AdGroupAssetService", "mutate_ad_group_assets"
            else: typ, svc_name, method = "CustomerAssetOperation", "CustomerAssetService", "mutate_customer_assets"
            remove_op = self.client.get_type(typ, version="v25"); remove_op.remove = link["resource_name"]
            svc = self.client.get_service(svc_name, version="v25")
            getattr(svc, method)(customer_id=self.customer_id, operations=[remove_op])
        return {"resource_name": created, "action": "RECREATED_SITELINK", "new_links": created_links,
                "removed_links": [x["resource_name"] for x in links]}


def load_client(config: Path):
    try:
        from google.ads.googleads.client import GoogleAdsClient
    except ModuleNotFoundError as exc:
        raise SystemExit("Falta google-ads. Instalar con: .venv-ads/bin/pip install -r requirements-ads.txt") from exc
    if not config.exists():
        raise SystemExit(f"Falta configuración privada: {config}. Copia config/google-ads.example.yaml y completa OAuth.")
    return GoogleAdsClient.load_from_storage(str(config), version="v25")


def write_report(payload: dict[str, Any], requested: Path | None = None) -> Path:
    path = requested or ROOT / "reports" / f"ads-url-sync-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
    return path


def mark_status(path: Path, change_id: str, status: str) -> None:
    with path.open(encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh)); fields = list(rows[0].keys()) if rows else list(UrlChange.__dataclass_fields__)
    for row in rows:
        if row.get("change_id") == change_id: row["status"] = status
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields); writer.writeheader(); writer.writerows(rows)


def parse_args():
    p = argparse.ArgumentParser(description="Synchronize Regalos Premium URL changes with Google Ads API v25")
    p.add_argument("--customer-id", default=os.getenv("GOOGLE_ADS_CUSTOMER_ID"))
    p.add_argument("--config", type=Path, default=Path(os.getenv("GOOGLE_ADS_CONFIGURATION_FILE", DEFAULT_CONFIG)))
    p.add_argument("--changes", type=Path, default=DEFAULT_CHANGES)
    p.add_argument("--change-id")
    p.add_argument("--include-future", action="store_true")
    p.add_argument("--apply", action="store_true", help="Actually mutate Google Ads. Default is dry-run.")
    p.add_argument("--report", type=Path)
    return p.parse_args()


def main() -> int:
    args = parse_args()
    if not args.customer_id: raise SystemExit("Falta --customer-id o GOOGLE_ADS_CUSTOMER_ID")
    changes = load_changes(args.changes, args.change_id, args.include_future)
    if not changes: raise SystemExit("No hay cambios READY/elegibles para procesar")
    client = load_client(args.config); sync = AdsSynchronizer(client, args.customer_id)
    report: dict[str, Any] = {"generated_at": datetime.now(timezone.utc).isoformat(), "mode": "APPLY" if args.apply else "DRY_RUN", "changes": []}
    overall_ok = True
    for change in changes:
        item: dict[str, Any] = {"change": asdict(change), "references": [], "results": [], "errors": []}
        try:
            refs = sync.inventory(change); item["references"] = [asdict(r) for r in refs]
            if args.apply:
                for ref in refs:
                    try: item["results"].append(sync.apply_reference(ref, change))
                    except Exception as exc: item["errors"].append({"resource_name": ref.resource_name, "error": str(exc)}); overall_ok = False
                if not item["errors"]: mark_status(args.changes, change.change_id, "APPLIED")
        except Exception as exc:
            item["errors"].append({"error": str(exc)}); overall_ok = False
        report["changes"].append(item)
    path = write_report(report, args.report)
    print(f"mode={report['mode']} changes={len(changes)} report={path}")
    for item in report["changes"]:
        print(f"{item['change']['change_id']}: refs={len(item['references'])} results={len(item['results'])} errors={len(item['errors'])}")
    return 0 if overall_ok else 1


if __name__ == "__main__":
    sys.exit(main())
