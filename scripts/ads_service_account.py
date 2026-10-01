#!/usr/bin/env python3
"""Shared, secret-safe configuration helpers for Google Ads service accounts."""
from __future__ import annotations

import json
import os
import stat
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = Path.home() / ".config" / "regalospremium" / "google-ads.yaml"
DEFAULT_CUSTOMER_ID = "5921822090"
PLACEHOLDER_PREFIX = "INSERT_"


def clean_customer_id(value: str) -> str:
    result = str(value).replace("-", "").strip()
    if not result.isdigit() or len(result) != 10:
        raise ValueError("customer_id debe contener exactamente 10 dígitos")
    return result


def default_config_path() -> Path:
    return Path(os.getenv("GOOGLE_ADS_CONFIGURATION_FILE_PATH", DEFAULT_CONFIG)).expanduser()


def _required_text(config: dict[str, Any], field: str) -> str:
    value = str(config.get(field, "")).strip()
    if not value or value.upper().startswith(PLACEHOLDER_PREFIX):
        raise ValueError(f"Falta {field} en la configuración privada")
    return value


def load_config(path: Path | None = None) -> dict[str, Any]:
    """Load only the service-account configuration; never print its content."""
    selected = (path or default_config_path()).expanduser()
    if not selected.is_file():
        raise FileNotFoundError(f"Falta configuración privada: {selected}")
    try:
        import yaml
    except ModuleNotFoundError as exc:
        raise RuntimeError("Falta PyYAML; instale requirements-ads.txt en .venv-ads") from exc
    data = yaml.safe_load(selected.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("La configuración debe ser un objeto YAML")
    if any(key in data for key in ("client_id", "client_secret", "refresh_token")):
        raise ValueError("Este flujo exige service account: retire campos OAuth de la configuración")
    config = dict(data)
    config["developer_token"] = _required_text(config, "developer_token")
    config["json_key_file_path"] = _required_text(config, "json_key_file_path")
    config["customer_id"] = clean_customer_id(config.get("customer_id", DEFAULT_CUSTOMER_ID))
    if config.get("login_customer_id"):
        config["login_customer_id"] = clean_customer_id(config["login_customer_id"])
    return config


def validate_key_file(config: dict[str, Any]) -> dict[str, str]:
    """Validate local key shape and permissions without logging any secret."""
    path = Path(config["json_key_file_path"]).expanduser()
    if not path.is_file():
        raise FileNotFoundError(f"No existe json_key_file_path: {path}")
    mode = stat.S_IMODE(path.stat().st_mode)
    if mode != 0o600:
        raise PermissionError(f"La clave debe tener chmod 600; actual={mode:03o}: {path}")
    try:
        key = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError("La clave de service account no es JSON válido") from exc
    if not isinstance(key, dict) or key.get("type") != "service_account":
        raise ValueError("El JSON debe ser una clave de tipo service_account")
    for field in ("client_email", "private_key", "token_uri"):
        if not str(key.get(field, "")).strip():
            raise ValueError(f"La clave de service account no contiene {field}")
    return {"key_path": str(path), "service_account_email": str(key["client_email"])}


def load_client(config: dict[str, Any]):
    """Import the network client lazily so parsing tests require no SDK."""
    try:
        from google.ads.googleads.client import GoogleAdsClient
    except ModuleNotFoundError as exc:
        raise RuntimeError("Falta google-ads. Instale: .venv-ads/bin/pip install -r requirements-ads.txt") from exc
    return GoogleAdsClient.load_from_dict(config)
