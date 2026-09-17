import csv
import importlib.util
import tempfile
import unittest
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("ads_url_sync", ROOT/"scripts/ads_url_sync.py")
m=importlib.util.module_from_spec(spec); sys.modules[spec.name]=m; spec.loader.exec_module(m)

class UrlSyncTests(unittest.TestCase):
    def test_replace_exact(self):
        new, hit=m.replace_url("https://regalospremium.cl/a.html","https://regalospremium.cl/a.html","https://regalospremium.cl/b.html")
        self.assertTrue(hit); self.assertEqual(new,"https://regalospremium.cl/b.html")
    def test_preserve_query(self):
        new, hit=m.replace_url("https://regalospremium.cl/a.html?utm_source=ads","https://regalospremium.cl/a.html","https://regalospremium.cl/b.html")
        self.assertTrue(hit); self.assertEqual(new,"https://regalospremium.cl/b.html?utm_source=ads")
    def test_no_path_match(self):
        new, hit=m.replace_url("https://regalospremium.cl/x.html","https://regalospremium.cl/a.html","https://regalospremium.cl/b.html")
        self.assertFalse(hit); self.assertEqual(new,"https://regalospremium.cl/x.html")
    def test_reject_external_host(self):
        c=m.UrlChange("X","1","https://example.com/a","https://regalospremium.cl/b","","READY","")
        with self.assertRaises(ValueError): m.validate_change(c)

if __name__ == "__main__": unittest.main()
