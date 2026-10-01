import importlib.util
import json
import os
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("ads_service_account", ROOT / "scripts" / "ads_service_account.py")
module = importlib.util.module_from_spec(spec); sys.modules[spec.name] = module; spec.loader.exec_module(module)


class ServiceAccountConfigTests(unittest.TestCase):
    def test_clean_customer_id(self):
        self.assertEqual(module.clean_customer_id("592-182-2090"), "5921822090")
        with self.assertRaises(ValueError): module.clean_customer_id("bad")

    def test_load_rejects_oauth(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "google-ads.yaml"
            path.write_text("json_key_file_path: /tmp/key.json\nclient_id: no\n", encoding="utf-8")
            with self.assertRaises(ValueError): module.load_config(path)

    def test_key_requires_0600_and_expected_shape(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "key.json"
            path.write_text(json.dumps({"type": "service_account", "client_email": "sa@example.invalid", "private_key": "not-a-real-key", "token_uri": "https://oauth2.googleapis.com/token"}), encoding="utf-8")
            os.chmod(path, 0o600)
            info = module.validate_key_file({"json_key_file_path": str(path)})
            self.assertEqual(info["service_account_email"], "sa@example.invalid")
            os.chmod(path, 0o644)
            with self.assertRaises(PermissionError):
                module.validate_key_file({"json_key_file_path": str(path)})

    def test_load_keyless_config_and_validate_source_token_mode(self):
        with tempfile.TemporaryDirectory() as directory:
            directory_path = Path(directory)
            token_path = directory_path / "gcp-user-token.json"
            token_path.write_text("private token content is not inspected here", encoding="utf-8")
            os.chmod(token_path, 0o600)
            config_path = directory_path / "google-ads.yaml"
            config_path.write_text(
                "auth_mode: impersonated_service_account\n"
                "target_service_account: sa@example.invalid\n"
                f"source_user_token_path: {token_path}\n"
                "customer_id: '592-182-2090'\n",
                encoding="utf-8",
            )
            config = module.load_config(config_path)
            self.assertEqual(config["customer_id"], "5921822090")
            self.assertNotIn("developer_token", config)
            self.assertEqual(module.validate_auth(config)["service_account_email"], "sa@example.invalid")
            os.chmod(token_path, 0o644)
            with self.assertRaises(PermissionError):
                module.validate_auth(config)

    def test_load_config_treats_developer_token_as_optional(self):
        with tempfile.TemporaryDirectory() as directory:
            directory_path = Path(directory)
            config_path = directory_path / "google-ads.yaml"
            config_path.write_text(
                "auth_mode: service_account_json\n"
                "json_key_file_path: /tmp/key.json\n"
                "developer_token: INSERT_DEVELOPER_TOKEN\n",
                encoding="utf-8",
            )
            self.assertNotIn("developer_token", module.load_config(config_path))

    def test_load_keyless_client_passes_optional_developer_token_as_none(self):
        credentials = object()
        google_client = mock.Mock()
        client_module = types.ModuleType("google.ads.googleads.client")
        client_module.GoogleAdsClient = google_client
        with (
            mock.patch.object(module, "create_impersonated_credentials", return_value=credentials),
            mock.patch.dict(sys.modules, {"google.ads.googleads.client": client_module}),
        ):
            module.load_client({"auth_mode": module.AUTH_MODE_IMPERSONATED})
        google_client.assert_called_once_with(
            credentials=credentials,
            developer_token=None,
            login_customer_id=None,
            use_proto_plus=True,
        )

    def test_impersonated_credentials_are_ads_scoped_without_network(self):
        source_credentials = object()
        result_credentials = object()
        user_credentials = mock.Mock()
        user_credentials.Credentials.from_authorized_user_file.return_value = source_credentials
        impersonated_credentials = mock.Mock()
        impersonated_credentials.Credentials.return_value = result_credentials
        config = {
            "source_user_token_path": "/private/token.json",
            "target_service_account": "sa@example.invalid",
        }
        with mock.patch.object(module, "_google_auth_modules", return_value=(impersonated_credentials, user_credentials)):
            result = module.create_impersonated_credentials(config)
        self.assertIs(result, result_credentials)
        user_credentials.Credentials.from_authorized_user_file.assert_called_once_with("/private/token.json")
        impersonated_credentials.Credentials.assert_called_once_with(
            source_credentials=source_credentials,
            target_principal="sa@example.invalid",
            target_scopes=["https://www.googleapis.com/auth/adwords"],
            lifetime=3600,
        )
