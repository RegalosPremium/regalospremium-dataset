import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("ads_generic_dry_run", ROOT / "scripts" / "ads_generic_dry_run.py")
module = importlib.util.module_from_spec(spec); sys.modules[spec.name] = module; spec.loader.exec_module(module)


class GenericDryRunTests(unittest.TestCase):
    def test_repository_inputs_build_offline_plan(self):
        keywords = module.read_csv(ROOT / "data/ads/ads_generic_keywords.csv", {"keyword", "match_type", "ad_group", "final_url", "status"})
        assets = module.read_csv(ROOT / "data/ads/ads_rsa_generic_assets.csv", {"asset_type", "text", "char_count", "status"})
        targets = module.read_csv(ROOT / "data/ads/ads_dsa_targets.csv", {"url", "label", "status"})
        plan = module.build_plan(keywords, assets, targets)
        self.assertEqual(plan["mode"], "DRY_RUN_ONLY")
        self.assertEqual(plan["mutations_sent"], 0)
        self.assertGreater(len(plan["proposed"]["keywords"]), 0)

    def test_rejects_outside_host(self):
        with self.assertRaises(ValueError): module.validate_url("https://example.com/", "test")
