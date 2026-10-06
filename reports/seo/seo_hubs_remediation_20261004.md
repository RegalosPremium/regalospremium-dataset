# Implementación hubs SEO B2B — 2026-10-04

> Evidencia histórica. La selección de productos y el sitemap vigentes fueron reemplazados por `reports/seo/seo_riskfix_20261006.json`, `reports/seo/seo_hubs_qa_20261006.json` y `reports/sitemap/sitemap_audit_latest.json`.

## Producción

Se crearon dos categorías/landings canónicas en PrestaShop:

- ID 140 — https://regalospremium.cl/regalos-corporativos/
  - H1: Regalos corporativos para empresas
  - Title: Regalos Corporativos para Empresas en Chile
  - Intenciones propietarias: regalos corporativos; regalos para empresas; regalos corporativos por mayor; regalos corporativos premium; regalos corporativos chile.
  - 12 productos activos asociados, sin cambiar su categoría por defecto.

- ID 141 — https://regalospremium.cl/regalos-publicitarios/
  - H1: Regalos publicitarios personalizados
  - Title: Regalos Publicitarios y Merchandising Corporativo
  - Intenciones propietarias: regalos publicitarios; regalos publicitarios por mayor; merchandising corporativo; regalos publicitarios chile.
  - 12 productos activos asociados, sin cambiar su categoría por defecto.

Las descripciones incluyen enlaces internos contextuales hacia categorías fuertes y mantienen el modelo B2B sin precios públicos.

## QA

reports/seo/seo_hubs_qa_20261004.json:

- 2/2 HTTP 200.
- 2/2 canonical exacto.
- 2/2 indexables, sin noindex.
- 12 asociaciones de producto por hub.
- 1 aparición exacta de cada hub en 1_es_0_sitemap.xml.
- Intenciones principales presentes en contenido.
- Resultado global: PASS.

Los 24 cambios de asociación de producto preservaron id_category_default, active e indexed. Evidencia: reports/seo/seo_hub_product_associations_20261004.json.

## Sitemap / GSC

Backup previo:
/home/maxdaguzan/RegalosPremium_Backups/seo_hubs_20261004/1_es_0_sitemap.before.xml

Sitemap publicado con ambos hubs: 1373 entradas.

GSC recibió nuevamente:
- 1_es_0_sitemap.xml — HTTP 204.
- 1_index_sitemap.xml — HTTP 204.

Al cierre ambos figuran isPending=true, warnings 0, errors 0.

## Repartición de intención

Registro canónico:
data/seo/seo_intent_hubs_20261004.csv

El dataset Ads se alinea con los hubs:
- corporativo → /regalos-corporativos/
- publicitario/merchandising → /regalos-publicitarios/

No se publicó ni activó ninguna campaña de Google Ads.

## Rollback

No se borró ningún objeto.

- Las categorías nuevas son IDs 140 y 141: rollback = desactivar, no eliminar.
- Backup XML de cada uno de los 24 productos asociados:
  /home/maxdaguzan/RegalosPremium_Backups/seo_hubs_20261004/products/
- Backup de sitemap indicado arriba.
