# Mapeo histórico de Google Ads

Fuente analizada: export histórico de palabras clave del 9 de junio al 6 de julio de 2026.

## Resultado

- 3.376 filas de origen.
- 3.362 combinaciones únicas de keyword + concordancia + grupo.
- 33 grupos históricos.
- 2.634 keywords clasificadas como PRODUCTO.
- 721 como USO_CAMPAÑA.
- 7 filas técnicas/vacías como DESCARTAR.
- 50 URLs históricas distintas.

## Arquitectura objetivo

Las keywords de producto se conectan a la taxonomía canónica `macroárea -> familia`.
Los materiales y temporadas no crean nuevas familias. Se conservan como intención transversal.
El blueprint incluye las 49 familias; las que no tienen demanda histórica quedan en `HOLD_NO_HISTORICAL_KEYWORDS`.

## Resolución de URLs

`entity_key` es la unión entre Ads y el catálogo. PrestaShop resolverá la URL vigente de cada familia/producto/landing.
Ningún cambio de URL se aplica desde este dataset por sí solo. La sincronización con Google Ads sigue siendo dry-run por defecto.

## Archivos

- `data/ads/ads_intent_mapping.csv`: keyword -> intención/familia.
- `data/ads/ads_group_mapping.csv`: resumen de grupos históricos.
- `data/ads/ads_url_inventory.csv`: inventario de URLs históricas.
- `data/ads/ads_campaign_blueprint.csv`: estructura objetivo.
- `reports/ads/ads_mapping_summary.json`: métricas de consolidación.

## Cierre de landings (17-09-2026)

Las 49 familias tienen una decisión explícita en `data/ads/ads_landing_decisions.csv`:

- 45 familias en `READY_URL`.
- 4 familias en `HOLD_*` por falta de una landing segura o por intención dividida.
- 0 familias en `WAIT_*`.

El generador del blueprint consume este registro para que un rebuild no reabra decisiones ya cerradas.
