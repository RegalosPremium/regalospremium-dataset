# GSC — Página alternativa con etiqueta canónica adecuada — 2026-10-03

Fuente: Coverage-Drilldown exportado desde GSC, 27 URLs.

## Clasificación
- 19 variantes con parámetros de orden/paginación: comportamiento correcto; canonical apunta a la versión limpia o paginada correspondiente. No se modifican.
- 1 alias Bamboo: ya estaba resuelto por 301 a /regalos-corporativos-bambu/.
- 6 aliases limpios legacy: convertidos de HTTP 200 + canonical a 301 directo hacia la categoría canónica.
- 1 caso /llaveros-metalicos/: no era un alias legítimo; era una colisión de resolución de sturls. La URL servía category-id-66 (Llaveros Cuero) pese a existir category-id-127 activa (Llaveros Metalicos) con 19 productos. Se corrigió por rewrite interno exacto a id_category=127, conservando la URL comercial.

## 301 aplicados
- /publicitarios-ecofriendly/ -> /productos-eco-friendly-publicitarios/
- /boligrafos-funcionales-y-destacadores/ -> /boligrafos-funcionales-y-destacadores-publicitarios/
- /boligrafos-cuerpo-blanco/ -> /boligrafos-cuerpo-blanco-publicitarios/
- /mugs-termos-sublimacion/ -> /mugs-y-termos-para-sublimacion-publicitarios/
- /boligrafos-cuerpo-color/ -> /boligrafos-cuerpo-color-publicitarios/
- /boligrafos-cuerpo-plateado/ -> /boligrafos-cuerpo-plateado-publicitarios/

## Llaveros Metálicos
Antes:
- /llaveros-metalicos/ = HTTP 200
- contenido servido: category-id-66
- H1: Llaveros Cuero
- canonical: /llaveros-cuero/

Después:
- /llaveros-metalicos/ = HTTP 200
- contenido servido: category-id-127
- H1: Llaveros Metalicos
- canonical: https://regalospremium.cl/llaveros-metalicos/

La categoría 127 permanece activa y contiene 19 relaciones de producto.

## Sitemap
Los seis aliases legacy no están en el sitemap y sus URLs canónicas sí.
- /llaveros-metalicos/ sí está en el sitemap y ahora su canonical es autoconsistente.

## robots/query variants
Las 19 variantes con order/page se mantienen como variantes de navegación con canonical adecuado. No se introducen redirects que destruyan paginación.

## QA
- .htaccess productivo actualizado por FTPS.
- data/seo_redirects.csv actualizado con los seis 301.
- validate_url_ecosystem.py: RC=0.
- No DELETE.
- No cambios de producto.
- No commit/push.

## Rollback
Backup inmediato previo:
- /home/maxdaguzan/RegalosPremium_Backups/gsc_fix_20261003/.htaccess.before_canonical_alt
