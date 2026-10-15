import csv,importlib.util,subprocess,tempfile,unittest,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('sitemap_validator',ROOT/'scripts/validate_sitemap.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
class SeoIntegrity(unittest.TestCase):
 def test_distributed_sitemap_matches_all_products(self):
  with (ROOT/'data/productos.csv').open(encoding='utf-8-sig',newline='') as f:catalog=list(csv.DictReader(f))
  self.assertEqual(mod.compare(catalog,(ROOT/'dist/sitemap-products.xml').read_bytes())['status'],'PASS')
 def test_sitemap_rejects_missing_extra_and_duplicate_urls(self):
  xml=b'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>https://regalospremium.cl/a</loc></url><url><loc>https://regalospremium.cl/a</loc></url></urlset>'
  r=mod.compare([{'url':'https://regalospremium.cl/b'}],xml)
  self.assertEqual(r['status'],'RISK');self.assertEqual(r['sitemap_duplicates'],1);self.assertEqual(len(r['missing']),1);self.assertEqual(len(r['extra']),1)
 def mutation(self,script,mutate):
  with tempfile.TemporaryDirectory() as d:
   r=Path(d);shutil.copytree(ROOT/'data',r/'data');shutil.copytree(ROOT/'scripts',r/'scripts');mutate(r)
   return subprocess.run(['python3',str(r/'scripts'/script)],capture_output=True,text=True).returncode
 def test_duplicate_url_is_fatal(self):
  def mutate(r):
   p=r/'data/productos.csv'
   with p.open(newline='') as f:a=list(csv.DictReader(f))
   a[1]['url']=a[0]['url']
   with p.open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(a[0]));w.writeheader();w.writerows(a)
  self.assertNotEqual(self.mutation('validate_dataset.py',mutate),0)
 def test_undocumented_editorial_owner_exception_is_fatal(self):
  def mutate(r):
   p=r/'data/seo/seo_hub_editorial_exceptions.csv';p.write_text(p.read_text().splitlines()[0]+'\n')
  self.assertNotEqual(self.mutation('validate_seo_hubs.py',mutate),0)
if __name__=='__main__':unittest.main()
