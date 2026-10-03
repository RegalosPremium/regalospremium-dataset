# Auditoría GSC desde exportes reales — 2026-10-03

Fuente maestra: `/home/maxdaguzan/regalospremium-dataset/data/gsc/coverage_drilldown_20261003_master.csv`. Filas auditadas: **176**.

## Estado de acceso GSC

La identidad exigida (`rp-google-ads-cli@able-marking-493221-m5.iam.gserviceaccount.com`) no está disponible en `CLOUDSDK_CONFIG=/home/maxdaguzan/.config/gcloud-rp-explorer`; detalle: `ERROR: (gcloud.auth.print-access-token) Your current active account [rp-google-ads-cli@able-marking-493221-m5.iam.gserviceaccount.com] does not have any valid credentials
Please run:

  $ gcloud auth login

to obtain new credentials.

For service account, please activate it first:

  $ gcloud auth activate-service-account ACCOUNT`. No se inició OAuth ni se usó otra identidad. Por ello URL Inspection y Search Analytics quedan explícitamente como evidencia insuficiente.

## Conteos PASS / PENDING / RISK por clase GSC

- Bloqueada por robots.txt: PASS 136, PENDING 0, RISK 0
- Página alternativa con etiqueta canónica adecuada: PASS 27, PENDING 0, RISK 0
- Duplicada: Google ha elegido una versión canónica diferente a la del usuario: PASS 0, PENDING 1, RISK 0
- Excluida por una etiqueta "noindex": PASS 1, PENDING 0, RISK 0
- No se ha encontrado (404): PASS 1, PENDING 5, RISK 5

Sitemap live GET: HTTP 200; 1369 URLs únicas. robots.txt GET: HTTP 200.

## Las 11 URLs 404 — evidencia completa

### https://regalospremium.cl/bolsos-y-mochilas-publicitarios/mochila-picnic.html

- HTTP/cadena: `301 https://regalospremium.cl/bolsos-y-mochilas-publicitarios/mochila-picnic.html -> 404 https://regalospremium.cl/greda/mochila-picnic.html`
- Sitemap vigente: no; regla redirects: ninguna.
- Canonical actual/esperada: `ninguna` / `sin match`.
- PrestaShop GET: product link_rewrite exact; ID 1022, ref. K4, active/indexed 0/0.
- GSC Inspection / Search Analytics: NOT_QUERIED_SERVICE_ACCOUNT_UNAVAILABLE / NOT_QUERIED_SERVICE_ACCOUNT_UNAVAILABLE; último rastreo exportado: 2026-09-19.
- **RISK** — acción candidata: candidata a baja; conservar 404 y retirar de sitemap si apareciera; revisión humana.

### https://regalospremium.cl/publicitarios-belleza-y-salud/deluxe-billetera-de-cuero-color-cafe-.html

- HTTP/cadena: `404 https://regalospremium.cl/publicitarios-belleza-y-salud/deluxe-billetera-de-cuero-color-cafe-.html`
- Sitemap vigente: no; regla redirects: ninguna.
- Canonical actual/esperada: `ninguna` / `https://regalospremium.cl/publicitarios-belleza-y-salud/`.
- PrestaShop GET: category link_rewrite exact; ID category:45, ref. —, active/indexed 1/—.
- GSC Inspection / Search Analytics: NOT_QUERIED_SERVICE_ACCOUNT_UNAVAILABLE / NOT_QUERIED_SERVICE_ACCOUNT_UNAVAILABLE; último rastreo exportado: 2026-09-18.
- **PENDING** — acción candidata: 301 candidata hacia categoría activa https://regalospremium.cl/publicitarios-belleza-y-salud/ sólo tras validar equivalencia semántica.

### https://regalospremium.cl/bolsas-publicitarias-con-logotipo/bolsa-algodon-manijas-colores-reutilizable.html

- HTTP/cadena: `404 https://regalospremium.cl/bolsas-publicitarias-con-logotipo/bolsa-algodon-manijas-colores-reutilizable.html`
- Sitemap vigente: no; regla redirects: ninguna.
- Canonical actual/esperada: `ninguna` / `https://regalospremium.cl/bolsas-publicitarias-con-logotipo/`.
- PrestaShop GET: category link_rewrite exact; ID category:15, ref. —, active/indexed 1/—.
- GSC Inspection / Search Analytics: NOT_QUERIED_SERVICE_ACCOUNT_UNAVAILABLE / NOT_QUERIED_SERVICE_ACCOUNT_UNAVAILABLE; último rastreo exportado: 2026-09-01.
- **PENDING** — acción candidata: 301 candidata hacia categoría activa https://regalospremium.cl/bolsas-publicitarias-con-logotipo/ sólo tras validar equivalencia semántica.

### https://regalospremium.cl/regalos-publicitarios-para-viajes-y-vacaciones/mesa-plegable-de-picnic.html

- HTTP/cadena: `404 https://regalospremium.cl/regalos-publicitarios-para-viajes-y-vacaciones/mesa-plegable-de-picnic.html`
- Sitemap vigente: no; regla redirects: ninguna.
- Canonical actual/esperada: `ninguna` / `https://regalospremium.cl/regalos-publicitarios-para-viajes-y-vacaciones/`.
- PrestaShop GET: category link_rewrite exact; ID category:80, ref. —, active/indexed 1/—.
- GSC Inspection / Search Analytics: NOT_QUERIED_SERVICE_ACCOUNT_UNAVAILABLE / NOT_QUERIED_SERVICE_ACCOUNT_UNAVAILABLE; último rastreo exportado: 2026-08-24.
- **PENDING** — acción candidata: 301 candidata hacia categoría activa https://regalospremium.cl/regalos-publicitarios-para-viajes-y-vacaciones/ sólo tras validar equivalencia semántica.

### https://regalospremium.cl/publicitarios-bamboo/set-escritura-bambu-boligrafo-portaminas-deluxe.html

- HTTP/cadena: `301 https://regalospremium.cl/publicitarios-bamboo/set-escritura-bambu-boligrafo-portaminas-deluxe.html -> 404 https://regalospremium.cl/regalos-corporativos-bambu/set-escritura-bambu-boligrafo-portaminas-deluxe.html`
- Sitemap vigente: no; regla redirects: {"old_url": "https://regalospremium.cl/publicitarios-bamboo/*", "new_url": "https://regalospremium.cl/regalos-corporativos-bambu/*", "http_code": "301", "status": "APPLIED", "effective_date": "2026-09-30", "reason": "Consolidación del subárbol Bamboo"}.
- Canonical actual/esperada: `ninguna` / `sin match`.
- PrestaShop GET: none; ID —, ref. —, active/indexed —/—.
- GSC Inspection / Search Analytics: NOT_QUERIED_SERVICE_ACCOUNT_UNAVAILABLE / NOT_QUERIED_SERVICE_ACCOUNT_UNAVAILABLE; último rastreo exportado: 2026-08-22.
- **PENDING** — acción candidata: corregir destino de regla 301 APPLIED; la cadena actual termina en 404.

### https://regalospremium.cl/merchandising-masivo/

- HTTP/cadena: `404 https://regalospremium.cl/merchandising-masivo/`
- Sitemap vigente: no; regla redirects: ninguna.
- Canonical actual/esperada: `https://regalospremium.cl/merchandising-masivo/` / `https://regalospremium.cl/merchandising-masivo/`.
- PrestaShop GET: category link_rewrite exact; ID category:124, ref. —, active/indexed 0/—.
- GSC Inspection / Search Analytics: NOT_QUERIED_SERVICE_ACCOUNT_UNAVAILABLE / NOT_QUERIED_SERVICE_ACCOUNT_UNAVAILABLE; último rastreo exportado: 2026-08-21.
- **RISK** — acción candidata: candidata a baja; conservar 404 y retirar de sitemap si apareciera; revisión humana.

### https://regalospremium.cl/bolsos-y-mochilas-publicitarios/mochila-netech.html

- HTTP/cadena: `301 https://regalospremium.cl/bolsos-y-mochilas-publicitarios/mochila-netech.html -> 404 https://regalospremium.cl/greda/mochila-netech.html`
- Sitemap vigente: no; regla redirects: ninguna.
- Canonical actual/esperada: `ninguna` / `sin match`.
- PrestaShop GET: product link_rewrite exact; ID 1020, ref. K7, active/indexed 0/0.
- GSC Inspection / Search Analytics: NOT_QUERIED_SERVICE_ACCOUNT_UNAVAILABLE / NOT_QUERIED_SERVICE_ACCOUNT_UNAVAILABLE; último rastreo exportado: 2026-08-17.
- **RISK** — acción candidata: candidata a baja; conservar 404 y retirar de sitemap si apareciera; revisión humana.

### https://regalospremium.cl/boligrafos-metalicos-y-ejecutivos/boligrafo-negro-cobre-tinta-azul.html

- HTTP/cadena: `404 https://regalospremium.cl/boligrafos-metalicos-y-ejecutivos/boligrafo-negro-cobre-tinta-azul.html`
- Sitemap vigente: no; regla redirects: ninguna.
- Canonical actual/esperada: `ninguna` / `sin match`.
- PrestaShop GET: none; ID —, ref. —, active/indexed —/—.
- GSC Inspection / Search Analytics: NOT_QUERIED_SERVICE_ACCOUNT_UNAVAILABLE / NOT_QUERIED_SERVICE_ACCOUNT_UNAVAILABLE; último rastreo exportado: 2026-08-14.
- **RISK** — acción candidata: candidata a baja; conservar 404 y retirar de sitemap si apareciera; revisión humana.

### https://regalospremium.cl/regalos-publicitarios-para-invierno/

- HTTP/cadena: `200 https://regalospremium.cl/regalos-publicitarios-para-invierno/`
- Sitemap vigente: yes; regla redirects: ninguna.
- Canonical actual/esperada: `https://regalospremium.cl/regalos-publicitarios-para-invierno/` / `https://regalospremium.cl/regalos-publicitarios-para-invierno/`.
- PrestaShop GET: category link_rewrite exact; ID category:53, ref. —, active/indexed 1/—.
- GSC Inspection / Search Analytics: NOT_QUERIED_SERVICE_ACCOUNT_UNAVAILABLE / NOT_QUERIED_SERVICE_ACCOUNT_UNAVAILABLE; último rastreo exportado: 2026-06-06.
- **PASS** — acción candidata: conservar; canonical actual coincide.

### https://regalospremium.cl/publicitarios-ecofriendly/llavero-linterna-led-dinamo.html

- HTTP/cadena: `404 https://regalospremium.cl/publicitarios-ecofriendly/llavero-linterna-led-dinamo.html`
- Sitemap vigente: no; regla redirects: ninguna.
- Canonical actual/esperada: `ninguna` / `sin match`.
- PrestaShop GET: none; ID —, ref. —, active/indexed —/—.
- GSC Inspection / Search Analytics: NOT_QUERIED_SERVICE_ACCOUNT_UNAVAILABLE / NOT_QUERIED_SERVICE_ACCOUNT_UNAVAILABLE; último rastreo exportado: 2026-06-06.
- **RISK** — acción candidata: candidata a baja; conservar 404 y retirar de sitemap si apareciera; revisión humana.

### https://regalospremium.cl/publicitarios-bamboo/pendrive-4gb-de-bamboo.html

- HTTP/cadena: `301 https://regalospremium.cl/publicitarios-bamboo/pendrive-4gb-de-bamboo.html -> 301 https://regalospremium.cl/regalos-corporativos-bambu/pendrive-4gb-de-bamboo.html -> 404 https://regalospremium.cl/greda/pendrive-4gb-de-bamboo.html`
- Sitemap vigente: no; regla redirects: {"old_url": "https://regalospremium.cl/publicitarios-bamboo/*", "new_url": "https://regalospremium.cl/regalos-corporativos-bambu/*", "http_code": "301", "status": "APPLIED", "effective_date": "2026-09-30", "reason": "Consolidación del subárbol Bamboo"}.
- Canonical actual/esperada: `ninguna` / `sin match`.
- PrestaShop GET: product link_rewrite exact; ID 70, ref. B58, active/indexed 0/0.
- GSC Inspection / Search Analytics: NOT_QUERIED_SERVICE_ACCOUNT_UNAVAILABLE / NOT_QUERIED_SERVICE_ACCOUNT_UNAVAILABLE; último rastreo exportado: 2026-05-13.
- **PENDING** — acción candidata: corregir destino de regla 301 APPLIED; la cadena actual termina en 404.

## Otras 165 URLs

- robots.txt: 136 URL(s); bloqueos deliberados 136, potencialmente problemáticos 0.
- canonical adecuada: 27 URL(s), PASS por la clasificación explícita de GSC; no se infiere que sean error.

- Duplicada: Google ha elegido una versión canónica diferente a la del usuario: `https://regalospremium.cl/botellas-metalicas-publicitarias/mug-termico-giant-1200cc-con-bombilla.html` — HTTP 200, canonical `https://regalospremium.cl/botellas-metalicas-publicitarias/mug-termico-giant-1200cc-con-bombilla.html`, noindex false; **PENDING**: revisar canonical declarada vs Google y señales internas.
- Excluida por una etiqueta "noindex": `https://regalospremium.cl/content/politica-de-privacidad` — HTTP 200, canonical `ausente`, noindex true; **PASS**: conservar noindex deliberado.

## Lote candidato (sin ejecución)

El CSV `gsc_404_surgical_batch_20261003.csv` contiene exclusivamente recomendaciones; no se modificó sitemap, redirects, canonical ni PrestaShop.
