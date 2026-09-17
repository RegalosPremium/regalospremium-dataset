# Auditoría de conectividad del ecosistema — 2026-09-17

## Alcance

Cadena auditada: GA4 → GSC → PrestaShop → Google Ads, entendida como integración del ecosistema de medición, indexación, catálogo y publicidad.

## Resultado ejecutivo

Estado global: **PARCIAL / OPERATIVO CON 2 BLOQUEOS DE API**.

- PrestaShop → sitemap → GSC: **PASS**.
- GSC → inspección de URLs: **PASS**.
- PrestaShop → ecosistema GitHub: **PASS**.
- GA4 en el sitio: **PASS**.
- GA4 API en GSC Wizard: **BLOCKED** (scope Analytics no autorizado).
- Google Ads mapping/dataset: **PASS**.
- Google Ads API live: **BLOCKED** (credenciales no configuradas).

## Evidencia

### GA4 / GTM

- GA4 detectado en HOME: `G-YZYXP2761X`.
- Google Tag Manager detectado: `GTM-N2MWGJR`.
- La web carga `gtag()` y `googletagmanager.com`.
- GSC Wizard está autenticado con `ventas@regalospremium.cl`, pero sin scope de Google Analytics; por ello no puede leer la propiedad GA4 ni cruzar GA4↔GSC todavía.

### Google Search Console

- Propiedad activa: `sc-domain:regalospremium.cl`.
- `1_index_sitemap.xml` y `1_es_0_sitemap.xml` ya estaban registrados.
- Sitemap regenerado el 17-09-2026: 1.372 URLs / 1.370 únicas.
- Catálogo activo: 1.289 productos; cobertura por slug: 1.289/1.289; faltantes: 0.
- Muestra de 9 URLs antes ausentes del sitemap: 6 `Submitted and indexed`, 3 `URL is unknown to Google`.

### PrestaShop

- Webservice live ya validado en lectura.
- Último sync live: 1.325 productos recibidos, 1.289 activos, 1.289 presentes en GitHub.
- Drift activo PrestaShop↔GitHub: 0.
- Categorías desconocidas nuevas: 0.
- Sitemap nativo regenerado correctamente y consistente con catálogo activo.

### Google Ads

- Mapping histórico validado: 3.362 keywords, 49 familias, 45 `READY_URL`, 4 `HOLD`, 0 `WAIT`.
- Conector `ads_url_sync.py` construido y validado en dry-run.
- No existe `config/google-ads.yaml` local ni variables de entorno `GOOGLE_ADS_CUSTOMER_ID` / `GOOGLE_ADS_DEVELOPER_TOKEN`.
- No se detecta etiqueta `AW-*` embebida directamente en el HTML de HOME; como existe GTM, esto no descarta que Ads/Conversion Tracking se cargue desde el contenedor.

## Diagnóstico de arquitectura

La topología real no es una cadena lineal. PrestaShop publica el sitio; GA4 y GSC observan el sitio en paralelo; Google Ads consume landings/conversiones y el sincronizador de URLs usa el catálogo GitHub/PrestaShop. Los dos cierres pendientes para observabilidad completa son: autorizar GA4 en la integración y autenticar Google Ads API.
