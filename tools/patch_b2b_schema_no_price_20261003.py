from pathlib import Path
import shutil, re, hashlib

BASE=Path("/home/maxdaguzan/RegalosPremium_Backups/gsc_schema_fix_20261003")
files={
"module": BASE/"modules/schemaproduct/schemaproduct.php",
"product": BASE/"themes/transformer/templates/catalog/product.tpl",
"prices": BASE/"themes/transformer/templates/catalog/_partials/product-prices.tpl",
"mini": BASE/"themes/transformer/templates/catalog/_partials/miniatures/product.tpl",
"mini_price": BASE/"themes/transformer/templates/catalog/_partials/miniatures/product-price.tpl",
"compact": BASE/"themes/transformer/templates/catalog/_partials/miniatures/product-slider-item-compact.tpl",
}
for p in files.values():
    if not p.exists(): raise SystemExit(f"MISSING {p}")

# 1) Custom module: keep installed but emit no Product/Offer JSON-LD for B2B catalog without public price.
src=files["module"].read_text(encoding="utf-8")
patched=re.sub(r"public function hookDisplayHeader\(\$params\)\s*\{.*?\n    \}\n\}",'''public function hookDisplayHeader($params)
    {
        // B2B catalog: public prices are intentionally not exposed.
        // Google Product/Merchant rich results require a price/review signal.
        // Emitting Product/Offer without price creates invalid GSC enhancements,
        // so this module deliberately emits no product commerce schema.
        return '';
    }
}''',src,flags=re.S)
if patched==src: raise SystemExit("MODULE_PATCH_FAILED")
patched=patched.replace("$this->version = '1.0.3';","$this->version = '1.0.4';")
patched=patched.replace("$this->displayName = 'Schema.org Producto sin Precio';","$this->displayName = 'Schema.org B2B sin Precio';")
patched=patched.replace("$this->description = 'Inyecta JSON-LD de producto con offers sin precio para SEO semantico.';","$this->description = 'Evita Product/Offer inválido en catálogo B2B sin precios públicos.';")
out=files["module"].with_suffix(".php.patched"); out.write_text(patched,encoding="utf-8")

# 2) Main Product microdata only when a public price is actually shown.
p=files["product"]; s=p.read_text(encoding="utf-8")
old='{if $sttheme.google_rich_snippets} itemscope itemtype="https://schema.org/Product" {/if}'
new='{if $sttheme.google_rich_snippets && $product.show_price} itemscope itemtype="https://schema.org/Product" {/if}'
if s.count(old)!=1: raise SystemExit(f"PRODUCT_COUNT={s.count(old)}")
p.with_suffix(".tpl.patched").write_text(s.replace(old,new,1),encoding="utf-8")

# 3) Price template: never emit Offer microdata if public price is hidden.
p=files["prices"]; s=p.read_text(encoding="utf-8")
s2=s.replace('{if $sttheme.google_rich_snippets}', '{if $sttheme.google_rich_snippets && $product.show_price}')
if s2==s: raise SystemExit("PRICES_PATCH_FAILED")
p.with_suffix(".tpl.patched").write_text(s2,encoding="utf-8")

# 4) Related/miniature Product and Offer microdata: require show_price too.
p=files["mini"]; s=p.read_text(encoding="utf-8")
needle="&& (!isset($no_google_rich_snippets) || !$no_google_rich_snippets)"
s2=s.replace(needle, needle+" && $product.show_price")
if s2==s: raise SystemExit("MINI_PATCH_FAILED")
p.with_suffix(".tpl.patched").write_text(s2,encoding="utf-8")

p=files["mini_price"]; s=p.read_text(encoding="utf-8")
needle="&& (!isset($no_google_rich_snippets) || !$no_google_rich_snippets)"
s2=s.replace(needle, needle+" && $product.show_price")
if s2==s: raise SystemExit("MINI_PRICE_PATCH_FAILED")
p.with_suffix(".tpl.patched").write_text(s2,encoding="utf-8")

p=files["compact"]; s=p.read_text(encoding="utf-8")
needle="&& (!isset($no_google_rich_snippets) || !$no_google_rich_snippets)"
s2=s.replace(needle, needle+" && $product.show_price")
if s2==s: raise SystemExit("COMPACT_PATCH_FAILED")
p.with_suffix(".tpl.patched").write_text(s2,encoding="utf-8")

for key,p in files.items():
    ext=".php.patched" if key=="module" else ".tpl.patched"
    q=p.with_suffix(ext)
    print(key, "before",len(p.read_bytes()),hashlib.sha256(p.read_bytes()).hexdigest(),
          "after",len(q.read_bytes()),hashlib.sha256(q.read_bytes()).hexdigest())
