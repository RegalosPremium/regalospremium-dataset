# Correcciones y verificación SEO — 15-10-2026

Base: commit 1a869e1713cb65dfe0521be5292fe8079cb6a223. Catálogo contrastado con Webservice PrestaShop actual; sin cambios en campañas publicitarias pagadas.

## PASS

- Se incorporaron los 24 productos activos ausentes del dataset y se actualizaron nombres/referencias desde la API. Se clasificaron los 45 productos antes pendientes mediante su objeto y categoría. Se añadieron las familias Iluminación y Quitasoles, sin generar URLs por temporada o material.
- Se comprobaron cuatro duplicidades adicionales por referencia normalizada, nombre, características y ausencia de combinaciones. Se conservaron los productos 356, 539, 1292 y 1302; se desactivaron 30, 418, 1396 y 1430 con redirect_type=301-product. Las cuatro rutas antiguas redirigen 301 a fichas HTTP 200 con canonical propio. No se borraron productos, imágenes ni registros de pedidos.
- Resultado: 1.309 productos activos, 1.309 IDs y URLs únicas; 51 familias, cero productos sin clasificar. Registro completo producto→familia→hub en data/seo/seo_hub_catalog_coverage.csv.
- Se conservó la selección de 12 productos editoriales activos por hub, sin intersección. Las siete excepciones comerciales de familia quedan explícitas y validadas; no transfieren la propiedad SEO de la familia.
- Los hubs 140 y 141 incorporan navegación para las 51 familias y el texto «Campañas temáticas para promociones específicas». API read-back y HTML públicos verificados. Las dos asociaciones extra del hub 141 son productos inactivos y no forman parte de la selección editorial activa.
- Las cuatro familias antes HOLD y seis intenciones antes WAIT tienen destinos existentes de navegación. Se distinguen categorías amplias, hubs y destinos exactos; no se afirma que exista una landing exclusiva por familia. El generador conserva decisiones explícitas sin demanda histórica. No se publicaron anuncios ni presupuestos en Google Ads.
- B47/ID1362 responde 200 con canonical propio en /boligrafos-y-lapices-eco-publicitarios/set-de-escritura-de-bambu.html. Su antigua ruta Bamboo redirige 301 a la categoría Bamboo: se corrigió el registro histórico, sin cambiar la URL vigente del producto.
- Sitemap distribuido: 1.309 URLs, igualdad exacta con el catálogo. Sitemap PrestaShop regenerado a las 14:21:07 UTC: 1.396 URLs únicas, cobertura exacta 1.309/1.309, sin duplicados ni ausencias. No confundir inclusión en sitemap con indexación.
- GSC confirmó que los envíos del 06-10-2026 ya estaban procesados, sin errores ni advertencias. El sitemap actualizado se reenvió con HTTP 204 en ambos endpoints.
- README, manifest, empresa, llms.txt, documentación de indexación y QA actualizados. Validadores endurecidos: los duplicados y productos sin clasificación son errores; cobertura completa de productos y navegación por familias; excepciones editoriales explícitas; coherencia del sitemap distribuido; anomalías DB impiden un PASS global.
- Cinco validadores locales, compilación Python y cuatro pruebas de regresión PASS. Comprobación HTTP secuencial de 45 destinos PASS; QA público de ambos hubs PASS.

## Seguimiento posterior por MariaDB y límites externos

- PASS: las diez asociaciones huérfanas se eliminaron por MariaDB directo en una transacción InnoDB: respaldo de las diez filas y restauración SQL disponibles; guardas de cantidad, inexistencia de producto y conservación de 1.309 activos. COMMIT tras confirmar cero huérfanas. Lectura independiente de MariaDB y API PrestaShop confirman cero. Evidencia: reports/prestashop/orphan_repair_20261015.json.
- RISK: el hosting devolvió HTTP 508 («Límite de Procesos de Entrada alcanzado») durante el rastreo completo. Se detuvo la carga concurrente; los controles puntuales secuenciales posteriores pasaron. No se acredita HTTP/canonical/indexabilidad o ausencia de contenido similar para las 1.309 fichas completas. La corrección de capacidad requiere diagnóstico del hosting, no cambiar cifras de un reporte.
- PENDING: los nuevos reenvíos GSC quedan isPending=true inmediatamente tras HTTP 204. El procesamiento y las decisiones de indexación dependen de Google; no se prometen ni se simulan.

## Evidencia vigente

- reports/prestashop/catalog_snapshot_20261015.json
- reports/prestashop/live_sync_latest.json y ecosystem_sync_latest.json
- reports/seo/catalog_refresh_20261015.json
- reports/seo/coverage_apply_20261015.json
- reports/seo/product_consolidation_20261015.json
- reports/seo/product_duplicate_redirect_qa_20261015.json
- reports/seo/seo_hubs_qa_latest.json
- reports/seo/targeted_live_qa_20261015.json
- reports/seo/catalog_http_partial_20261015.json
- reports/seo/sitemap_regeneration_20261015.json
- reports/sitemap/sitemap_audit_latest.json
- reports/seo/gsc_sitemap_resubmit_20261015.json

## Recuperación

Respaldos de XML anteriores y posteriores en /home/maxdaguzan/RegalosPremium_Backups/product_consolidation_20261015/ y seo_hub_links_20261015/. El sitemap previo quedó en sitemap_riskfix_20261015_112105/. Los reportes contienen SHA-256 de las operaciones. Los respaldos privados no se publican en GitHub.
