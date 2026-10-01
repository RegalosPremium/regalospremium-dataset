import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

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
            path.write_text("developer_token: token\njson_key_file_path: /tmp/key.json\nclient_id: no\n", encoding="utf-8")
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
