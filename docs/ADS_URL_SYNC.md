# Sincronización de URLs: catálogo → Google Ads

## Objetivo
Evitar que un cambio de URL amigable deje referencias antiguas dispersas. GitHub registra cada cambio y `scripts/ads_url_sync.py` localiza y sincroniza sus referencias en Google Ads.

## Componentes
- `data/url_duplicates.csv`: inventario DUP-1..DUP-4; permanece `HOLD` hasta decidir slug y producto que conserva URL.
- `data/url_changes.csv`: cola ejecutable. Sólo filas `READY` y con fecha efectiva vigente entran al proceso.
- `scripts/register_url_change.py`: registra un cambio aprobado.
- `scripts/ads_url_sync.py`: inventario, dry-run, aplicación y reporte.
- `config/google-ads.yaml`: credenciales privadas; nunca se versiona.

## Entidades cubiertas
1. Anuncios: actualiza `final_urls` / `final_mobile_urls`.
2. Keywords: actualiza URLs a nivel de criterio.
3. Performance Max: actualiza `asset_group.final_urls`.
4. Sitelinks: crea un asset equivalente con URL nueva, conserva configuración/vínculos y retira los vínculos del asset anterior.
5. Cualquier asset con URL que no sea SITELINK se detecta y bloquea la aplicación automática para revisión, evitando cambios silenciosos.

## Seguridad operativa
El modo normal es `DRY_RUN`. No existe mutación sin `--apply`. Sólo se aceptan URLs HTTPS de `regalospremium.cl`; parámetros de tracking existentes se conservan.

## Flujo de un cambio
1. Definir cuál producto conserva la URL histórica y cuál recibe slug nuevo.
2. Preparar URL nueva y redirección 301 en PrestaShop.
3. Registrar el cambio como `READY` con fecha efectiva.
4. Ejecutar dry-run y revisar el reporte de referencias encontradas.
5. Ejecutar `--apply` cuando sitio/301 estén listos.
6. Regenerar sitemap e IndexNow delta; validar 200, canonical y 301.
7. El sincronizador marca la fila `APPLIED` sólo si no hubo errores de Ads.

## Conexión futura con PrestaShop
El siguiente adaptador leerá producto/slug/canonical desde PrestaShop y escribirá la cola de cambios y la BBDD operativa. La API de Ads queda desacoplada: consume cambios validados, no modifica directamente la base de PrestaShop.
