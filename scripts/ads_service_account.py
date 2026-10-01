#!/usr/bin/env python3
"""Secret-safe Google Ads authentication helpers (keyless preferred)."""
from __future__ import annotations

import json
import os
import stat
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = Path.home() / ".config" / "regalospremium" / "google-ads.yaml"
DEFAULT_CUSTOMER_ID = "5921822090"
PLACEHOLDER_PREFIX = "INSERT_"
ADWORDS_SCOPE = "https://www.googleapis.com/auth/adwords"
AUTH_MODE_IMPERSONATED = "impersonated_service_account"
AUTH_MODE_GCLOUD = "gcloud_impersonation"
AUTH_MODE_JSON = "service_account_json"


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
    """Load auth settings without printing configuration values or secrets."""
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
        raise ValueError("Use source_user_token_path; no incluya OAuth secrets en la configuración")

    config = dict(data)
    config["auth_mode"] = str(config.get("auth_mode", AUTH_MODE_JSON)).strip()
    if config["auth_mode"] not in (AUTH_MODE_IMPERSONATED, AUTH_MODE_GCLOUD, AUTH_MODE_JSON):
        raise ValueError("auth_mode debe ser impersonated_service_account, gcloud_impersonation o service_account_json")
    developer_token = str(config.get("developer_token", "")).strip()
    if developer_token and not developer_token.upper().startswith(PLACEHOLDER_PREFIX):
        config["developer_token"] = developer_token
    else:
        config.pop("developer_token", None)
    config["customer_id"] = clean_customer_id(config.get("customer_id", DEFAULT_CUSTOMER_ID))
    if config.get("login_customer_id"):
        config["login_customer_id"] = clean_customer_id(config["login_customer_id"])
    if config["auth_mode"] == AUTH_MODE_IMPERSONATED:
        config["target_service_account"] = _required_text(config, "target_service_account")
        config["source_user_token_path"] = _required_text(config, "source_user_token_path")
    elif config["auth_mode"] == AUTH_MODE_GCLOUD:
        config["target_service_account"] = _required_text(config, "target_service_account")
        config["gcloud_path"] = _required_text(config, "gcloud_path")
        config["gcloud_config_dir"] = _required_text(config, "gcloud_config_dir")
    else:
        config["json_key_file_path"] = _required_text(config, "json_key_file_path")
    return config


def _require_mode_0600(path: Path, label: str) -> None:
    if not path.is_file():
        raise FileNotFoundError(f"No existe {label}: {path}")
    mode = stat.S_IMODE(path.stat().st_mode)
    if mode != 0o600:
        raise PermissionError(f"{label} debe tener chmod 600; actual={mode:03o}: {path}")


def validate_key_file(config: dict[str, Any]) -> dict[str, str]:
    """Validate JSON-key fallback shape and permissions without logging secrets."""
    path = Path(config["json_key_file_path"]).expanduser()
    _require_mode_0600(path, "La clave")
    try:
        key = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError("La clave de service account no es JSON válido") from exc
    if not isinstance(key, dict) or key.get("type") != "service_account":
        raise ValueError("El JSON debe ser una clave de tipo service_account")
    for field in ("client_email", "private_key", "token_uri"):
        if not str(key.get(field, "")).strip():
            raise ValueError(f"La clave de service account no contiene {field}")
    return {"auth_mode": AUTH_MODE_JSON, "service_account_email": str(key["client_email"])}


def validate_impersonation_token(config: dict[str, Any]) -> dict[str, str]:
    """Check only existence/mode of the private source token; never display it."""
    path = Path(config["source_user_token_path"]).expanduser()
    _require_mode_0600(path, "source_user_token_path")
    return {"auth_mode": AUTH_MODE_IMPERSONATED, "service_account_email": config["target_service_account"]}


def validate_gcloud(config: dict[str, Any]) -> dict[str, str]:
    gcloud = Path(config["gcloud_path"]).expanduser()
    cfg = Path(config["gcloud_config_dir"]).expanduser()
    if not gcloud.is_file():
        raise FileNotFoundError(f"No existe gcloud: {gcloud}")
    if not cfg.is_dir():
        raise FileNotFoundError(f"No existe gcloud_config_dir: {cfg}")
    return {"auth_mode": AUTH_MODE_GCLOUD, "service_account_email": config["target_service_account"]}


def validate_auth(config: dict[str, Any]) -> dict[str, str]:
    if config["auth_mode"] == AUTH_MODE_IMPERSONATED:
        return validate_impersonation_token(config)
    if config["auth_mode"] == AUTH_MODE_GCLOUD:
        return validate_gcloud(config)
    return validate_key_file(config)


def _google_auth_modules():
    from google.auth import impersonated_credentials
    from google.oauth2 import credentials as user_credentials
    return impersonated_credentials, user_credentials


def create_impersonated_credentials(config: dict[str, Any]):
    """Create short-lived Ads-scoped credentials from the private user token."""
    source_path = Path(config["source_user_token_path"]).expanduser()
    impersonated_credentials, user_credentials = _google_auth_modules()
    source_credentials = user_credentials.Credentials.from_authorized_user_file(str(source_path))
    return impersonated_credentials.Credentials(
        source_credentials=source_credentials,
        target_principal=config["target_service_account"],
        target_scopes=[ADWORDS_SCOPE],
        lifetime=3600,
    )


def create_gcloud_impersonated_credentials(config: dict[str, Any]):
    """Mint a short-lived Ads-scoped token via the official gcloud CLI."""
    from google.oauth2 import credentials as user_credentials
    env = dict(os.environ)
    env["CLOUDSDK_CONFIG"] = str(Path(config["gcloud_config_dir"]).expanduser())
    cmd = [
        str(Path(config["gcloud_path"]).expanduser()),
        "auth", "print-access-token",
        f"--impersonate-service-account={config['target_service_account']}",
        f"--scopes={ADWORDS_SCOPE}",
    ]
    result = subprocess.run(cmd, env=env, capture_output=True, text=True, check=False, timeout=60)
    token = result.stdout.strip()
    if result.returncode != 0 or not token:
        msg = result.stderr.strip().splitlines()[-1] if result.stderr.strip() else "gcloud no emitió token"
        raise RuntimeError(f"Falló gcloud impersonation: {msg}")
    return user_credentials.Credentials(token=token, scopes=[ADWORDS_SCOPE])


def load_client(config: dict[str, Any]):
    """Create the Google Ads client lazily, using explicit keyless credentials."""
    try:
        from google.ads.googleads.client import GoogleAdsClient
    except ModuleNotFoundError as exc:
        raise RuntimeError("Falta google-ads. Instale: .venv-ads/bin/pip install -r requirements-ads.txt") from exc
    if config["auth_mode"] == AUTH_MODE_JSON:
        return GoogleAdsClient.load_from_dict(config)
    if config["auth_mode"] == AUTH_MODE_GCLOUD:
        credentials = create_gcloud_impersonated_credentials(config)
    else:
        credentials = create_impersonated_credentials(config)
    return GoogleAdsClient(
        credentials=credentials,
        developer_token=config.get("developer_token"),
        login_customer_id=config.get("login_customer_id"),
        use_proto_plus=bool(config.get("use_proto_plus", True)),
    )
