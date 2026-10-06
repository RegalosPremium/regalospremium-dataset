# Cierre de riesgos SEO — 2026-10-06

## PASS

- Hubs PrestaShop: categorías 140 y 141 responden HTTP 200, canonical propio, indexables y presentes una vez en sitemap.
- Selección editorial: 12 productos exactos por hub; 24 productos únicos; intersección cero.
- Cobertura: 49 de 49 familias tienen un único hub propietario en `data/seo/seo_hub_family_coverage.csv`.
- Intenciones: las 17 consultas genéricas de Ads tienen un único propietario; 34 combinaciones EXACT/PHRASE coinciden con el registro SEO.
- Ads/DSA: las intenciones corporativas apuntan a `/regalos-corporativos/`; publicitarias y merchandising a `/regalos-publicitarios/`; la home fue retirada como destino genérico.
- Duplicados: DUP-1 a DUP-4 figuran RESOLVED; las ocho URLs finales responden HTTP 200 con canonical propio.
- Catálogo: 1.289 productos, 1.289 URLs únicas.
- Sitemap: regenerado el 2026-10-06 17:10:59 UTC; 1.399 URLs, 1.399 únicas; cobertura exacta 1.289/1.289 productos.
- GSC: `1_index_sitemap.xml` y `1_es_0_sitemap.xml` aceptados con HTTP 204; warnings 0, errors 0.
- Validadores: `validate_dataset.py`, `validate_url_ecosystem.py`, `validate_ads_mapping.py` y `validate_seo_hubs.py` PASS.

## PENDING

- GSC mantiene ambos sitemaps en `isPending=true` inmediatamente después del reenvío; corresponde al procesamiento normal posterior a la aceptación HTTP 204.

## Evidencia

- `reports/seo/seo_riskfix_20261006.json`
- `reports/seo/seo_hubs_qa_20261006.json`
- `reports/seo/url_duplicates_liveqa_20261006.json`
- `reports/seo/catalog_url_canonical_sync_20261006.json`
- `reports/seo/sitemap_regeneration_20261006.json`
- `reports/seo/gsc_sitemap_resubmit_20261006.json`
- `reports/sitemap/sitemap_audit_latest.json`

## Rollback

- Productos: `/home/maxdaguzan/RegalosPremium_Backups/seo_riskfix_20261006_140402/`
- Sitemap previo: `/home/maxdaguzan/RegalosPremium_Backups/sitemap_riskfix_20261006_141056/`
