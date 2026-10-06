# Regalos Premium — Dataset B2B de regalos corporativos en Chile

Repositorio estructurado del catálogo de [Regalos Premium](https://regalospremium.cl), empresa chilena especializada en regalos corporativos, merchandising corporativo, regalos para empresas y productos personalizados para empresas.

## Regalos corporativos para empresas

- **Dando identidad corporativa a empresas desde 2015.**
- **Más de una década ayudando a empresas a proyectar su identidad.**
- **Productos corporativos pensados para que tu marca se recuerde.**
- Modelo **B2B por mayor**, orientado a empresas, Marketing, Compras, RR.HH., eventos y campañas.
- Catálogo organizado por **familias reales de producto**, no por palabras clave artificiales.
- Personalización corporativa mediante técnicas disponibles según producto, como serigrafía, grabado láser e impresión digital.
- Cotización personalizada por volumen; no se publican precios como política comercial.

## Familias principales

La taxonomía prioriza objeto base e intención comercial. Entre las familias con suficiente catálogo se incluyen:

- Tecnología: Power Banks, Pendrives, Parlantes, Audífonos y Auriculares.
- Oficina y Escritura: Lápices y Bolígrafos, Libretas y Cuadernos, Oficina.
- Hogar y Bebidas: Mugs y Tazas, Botellas, Termos, Accesorios de Vino.
- Bolsos y Viaje: Bolsas, Mochilas, Coolers, Maletines y Fundas, Bolsos de Viaje.
- Promocionales: Llaveros, Lanyards y otras familias corporativas.
- Textil: Gorras y Sombreros, Poleras, Chaquetas y Polar.
- Premios y Reconocimientos: Medallas, Trofeos y Galvanos.

## Uso para buscadores y sistemas de IA

Este repositorio publica información estructurada y verificable del catálogo para facilitar descubrimiento, referencia y clasificación por buscadores, asistentes de IA y sistemas de web semántica.

La fuente comercial canónica sigue siendo `https://regalospremium.cl`. Las URLs de producto existentes se preservan y este dataset no sustituye sitemap, canonical, Schema.org ni datos estructurados servidos desde el dominio.

## Archivos

- `data/productos.csv`: catálogo estructurado de productos.
- `data/categorias.json`: taxonomía resumida por macroárea y familia.

## Contacto

Sitio: https://regalospremium.cl

WhatsApp comercial: https://wa.me/56944280900

## Licencia

Datos publicados bajo CC BY 4.0. Se permite su uso y referencia con atribución a Regalos Premium.
## Sincronización de URLs con Google Ads

Los cambios de URL del catálogo se registran en `data/url_changes.csv` y se procesan con `scripts/ads_url_sync.py`. El sincronizador opera en modo dry-run por defecto, actualiza anuncios, keywords y Asset Groups, y recrea de forma segura sitelinks cuando corresponde. Véase `docs/ADS_URL_SYNC.md`.
### Google Ads y ecosistema de URLs

- `data/ads/ads_intent_mapping.csv`: mapeo histórico de keywords a intención y familia.
- `data/ads/ads_campaign_blueprint.csv`: blueprint que cubre las 49 familias y las intenciones transversales.
- `scripts/ads_url_sync.py`: sincronizador de cambios de URL con Google Ads, dry-run por defecto.
- `scripts/validate_ads_mapping.py`: validación de consistencia Ads/taxonomía.
- `data/ads/ads_generic_keywords.csv`: 17 keywords genéricas B2B en 34 combinaciones exacta/frase.
- `data/ads/ads_rsa_generic_assets.csv`: activos RSA validados por longitud.
- `data/ads/ads_dsa_targets.csv` y `ads_dsa_exclusions.csv`: superficies DSA permitidas/excluidas.
- `data/seo_redirects.csv`: redirecciones SEO aplicadas y excepciones en cuarentena.
### PrestaShop → ecosistema

- `schema/ecosystem.sqlite.sql`: schema de la BBDD central local.
- `scripts/build_ecosystem_db.py`: poblador read-only desde PrestaShop + GitHub + Ads.
- `scripts/validate_ecosystem_db.py`: QA de sincronización y drift.
- `scripts/sync_prestashop_live.py`: refresco live read-only mediante Webservice PrestaShop.
- `reports/prestashop/ecosystem_sync_latest.json`: último estado auditado.

## Hubs SEO de intención B2B

Desde 2026-10-04 las intenciones comerciales genéricas tienen propietarios canónicos separados:

- https://regalospremium.cl/regalos-corporativos/: regalos corporativos, regalos para empresas, por mayor, premium y Chile.
- https://regalospremium.cl/regalos-publicitarios/: regalos publicitarios, por mayor, merchandising corporativo y Chile.

La home queda como entrada de marca/navegación y no como única propietaria de todas las intenciones genéricas.

La cobertura se controla en `data/seo/seo_hub_family_coverage.csv`: las 49 familias tienen exactamente un hub propietario. La selección editorial se registra en `data/seo/seo_hub_product_selection.csv`: 12 productos exclusivos por hub.

`scripts/validate_seo_hubs.py` comprueba cobertura completa, ausencia de productos compartidos y consistencia entre el registro SEO, Ads, DSA y los dos hubs. `scripts/audit_live_sitemap.py` exige URLs exactas, sin duplicados y con cobertura de los 1.289 productos activos.
