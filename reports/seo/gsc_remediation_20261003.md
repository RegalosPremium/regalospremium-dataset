# GSC remediation — 2026-10-03

## Scope
Source master: 176 URLs exported directly from Google Search Console.
External changes were limited to SEO remediation benefiting regalospremium.cl. No product deletion, no Git commit/push.

## Coverage classes
- 11 Not found (404)
- 136 Blocked by robots.txt
- 27 Alternate page with proper canonical tag
- 1 Duplicate: Google chose different canonical
- 1 Excluded by noindex

## 404 remediation
Post-fix state:
- 9 legacy URLs now return a single 301 to a live semantically relevant URL and finish HTTP 200.
- 1 URL (/regalos-publicitarios-para-invierno/) was already live HTTP 200; GSC data is stale from its prior crawl.
- 1 URL (/merchandising-masivo/) remains intentional HTTP 404 because the category is inactive, has no equivalent landing, is absent from the sitemap, and had no Search Analytics traffic. An irrelevant redirect was not introduced.

Applied 301 targets:
- /bolsos-y-mochilas-publicitarios/mochila-picnic.html -> /mochilas/mochila-picnic-4-personas-accesorios-cooler.html
- /publicitarios-belleza-y-salud/deluxe-billetera-de-cuero-color-cafe-.html -> /billeteras-y-porta-documentos/billetera-deluxe-cuero-marron-broche.html
- /bolsas-publicitarias-con-logotipo/bolsa-algodon-manijas-colores-reutilizable.html -> /bolsas-de-algodon-publicitarias/bolsa-algodon-asas-colores.html
- /regalos-publicitarios-para-viajes-y-vacaciones/mesa-plegable-de-picnic.html -> /regalos-publicitarios-para-viajes-y-vacaciones/
- /publicitarios-bamboo/set-escritura-bambu-boligrafo-portaminas-deluxe.html -> /regalos-corporativos-bambu/
- /bolsos-y-mochilas-publicitarios/mochila-netech.html -> /bolsos-y-mochilas-publicitarios/
- /boligrafos-metalicos-y-ejecutivos/boligrafo-negro-cobre-tinta-azul.html -> /boligrafos-metalicos-y-ejecutivos-publicitarios/
- /publicitarios-ecofriendly/llavero-linterna-led-dinamo.html -> /llaveros-promocionales/llavero-linterna-led.html
- /publicitarios-bamboo/pendrive-4gb-de-bamboo.html -> /regalos-corporativos-bambu/

Exact overrides were also added for the two new-category Bamboo dead slugs so they cannot terminate in /greda/ 404.

## GSC verification
Direct API access used service-account impersonation with webmasters scopes.
URL Inspection was executed for the 11 404 URLs plus the canonical/noindex exceptions.
Search Analytics exact-page queries covered 2026-07-01 through 2026-09-30.

Observed traffic on the 404 set:
- /bolsas-publicitarias-con-logotipo/bolsa-algodon-manijas-colores-reutilizable.html: 0 clicks, 2 impressions.
- /boligrafos-metalicos-y-ejecutivos/boligrafo-negro-cobre-tinta-azul.html: 0 clicks, 2 impressions.
- all other inspected 404 URLs: 0 clicks, 0 impressions.

The duplicate-canonical URL currently reports googleCanonical == userCanonical and pageFetchState SUCCESSFUL. No site mutation was required.
The privacy-policy URL remains intentionally noindex; GSC reports BLOCKED_BY_META_TAG and it is absent from the live sitemap.

## robots.txt
136 GSC blocked URLs were reviewed as a class:
- 131 include the order parameter.
- remaining blocked URLs are private/technical controller, back parameter, login or account URLs.
No indexable content was found to be unintentionally blocked. robots.txt was not changed.

## Sitemaps
Both submitted sitemaps were resubmitted through the Search Console API after remediation:
- https://regalospremium.cl/1_es_0_sitemap.xml — HTTP 204 accepted.
- https://regalospremium.cl/1_index_sitemap.xml — HTTP 204 accepted.

GSC currently reports warnings=0, errors=0, isPending=true while Google fetches the refreshed submissions.
Live product sitemap contains 1,369 URLs.
None of the obsolete 404 product/category URLs is in the sitemap; the winter category is present and currently HTTP 200.

## QA
Post-deployment HTTP QA: 0 failures.
Sanity checks:
- homepage HTTP 200
- sitemap index HTTP 200
- robots.txt HTTP 200
- all 9 new redirect sources: first hop 301, final hop 200
- merchandising-masivo: intentional 404
- winter category: direct 200

URL ecosystem validator: RC=0.

## Backups and rollback
Original live .htaccess:
- /home/maxdaguzan/RegalosPremium_Backups/gsc_fix_20261003/.htaccess.live
Original redirect registry:
- /home/maxdaguzan/RegalosPremium_Backups/gsc_fix_20261003/seo_redirects.csv.before

Rollback consists of restoring .htaccess.live to www/.htaccess and restoring seo_redirects.csv.before locally.

## Evidence
- reports/seo/gsc_priority_inspection_20261003.json
- reports/seo/gsc_fix_qa_20261003.json
- reports/seo/gsc_sitemap_resubmit_20261003.json
- data/gsc/coverage_drilldown_20261003_master.csv
- data/seo_redirects.csv
