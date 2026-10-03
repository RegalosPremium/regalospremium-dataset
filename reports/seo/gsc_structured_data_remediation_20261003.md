# GSC structured-data remediation — 2026-10-03

## Source exports
Three direct GSC issue exports:
1. Merchant listings — 15 URLs — `Falta el campo "price" (en "offers")`.
2. Product snippets — 15 URLs — `Se debe especificar "price" o "priceSpecification.price" (en "offers")`.
3. Product snippets — 17 URLs — `Debe especificarse "offers", "review" o "aggregateRating"`.

Unique affected URLs: 17.

Consolidated source:
- `data/gsc/structured_data_issues_20261003.csv`

## Business rule preserved
Regalos Premium is B2B and intentionally does not publish product prices in JSON-LD or in the public catalog.
No synthetic/fake price, review or rating was added.

## Root cause
Two independent markup sources were making Google classify B2B pages as Product/Merchant rich-result candidates:

1. Custom module `modules/schemaproduct/schemaproduct.php` v1.0.3 emitted:
   - `@type: Product`
   - `offers: Offer`
   - `priceCurrency: CLP`
   - no `price`

2. Transformer theme emitted Product/Offer microdata even when the catalog price was hidden.

This combination generated both GSC issue families.

## Production remediation
### Custom module
`schemaproduct` updated to v1.0.4.
It remains installed but emits no Product/Offer commerce schema for the B2B no-price catalog.

### Transformer
Product/Offer rich-snippet microdata is now conditional on `$product.show_price` in:
- `themes/transformer/templates/catalog/product.tpl`
- `themes/transformer/templates/catalog/_partials/product-prices.tpl`
- `themes/transformer/templates/catalog/_partials/miniatures/product.tpl`
- `themes/transformer/templates/catalog/_partials/miniatures/product-price.tpl`
- `themes/transformer/templates/catalog/_partials/miniatures/product-slider-item-compact.tpl`

Organization/WebSite schema and normal SEO content remain intact.

## QA
Slow sequential production QA over all 17 GSC URLs:
- HTTP/final page usable: 17/17
- Product JSON-LD: 0/17
- Offer JSON-LD: 0/17
- Product/Offer microdata: 0/17
- JSON-LD parse errors: 0
- PASS: 17
- FAIL: 0

Evidence:
- `reports/seo/gsc_structured_data_qa_slow_20261003.json`
- `reports/seo/gsc_structured_data_qa_slow_20261003.log`

## Expected GSC behavior
The current GSC issue rows are historical crawl state. After recrawl, these pages should stop qualifying as invalid Merchant listings/Product snippets rather than becoming priced merchant listings.
Use GSC `Validar corrección` on each of the three issue groups after the production change.

## Backups / rollback
Original production copies are under:
`/home/maxdaguzan/RegalosPremium_Backups/gsc_schema_fix_20261003/`

No product data was deleted or repriced.
No fake price/review/rating was introduced.
