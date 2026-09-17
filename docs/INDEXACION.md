# Arquitectura de indexación

## Principio

GitHub es la fuente pública, versionada y legible por máquinas. No sustituye a `regalospremium.cl` como host canónico. Los artefactos que afectan al rastreo deben publicarse en el dominio principal.

## Google

- Mantener canonicals, sitemap y enlazado interno en `regalospremium.cl`.
- Publicar `Organization` JSON-LD en HOME o en una página corporativa adecuada.
- Usar datos estructurados `Product` en fichas individuales cuando la información visible de la página los respalde. Sin `offers`, `review` o `aggregateRating`, no se declara elegibilidad para fragmentos enriquecidos de producto.
- Enviar y mantener el sitemap mediante Search Console.

## Schema.org

`schema/organization.jsonld` declara la entidad Regalos Premium con:

- trayectoria comercial: "Dando identidad corporativa a empresas desde 2015.";
- modelo B2B;
- especialización en regalos corporativos y merchandising;
- canal de ventas/cotización.

Antes de desplegarlo en producción debe validarse y reflejar información visible y verdadera en el sitio.

## Yandex e IndexNow

- Yandex soporta IndexNow para avisar de URLs nuevas, modificadas o eliminadas.
- No se debe enviar todo el catálogo repetidamente: sólo cambios reales.
- La clave de IndexNow debe validarse desde `regalospremium.cl`, no desde GitHub.
- Mantener además un sitemap público y actualizado en el dominio.

`scripts/build_indexnow_payload.py` sólo construye el payload. No hace envíos por sí solo.

## Sitemap

`scripts/build_sitemap.py` genera `dist/sitemap-products.xml` a partir de las URLs únicas del catálogo. Ese archivo es un artefacto de despliegue: para tener efecto debe servirse desde `regalospremium.cl` y referenciarse donde corresponda.

## Anti-sobresegmentación

La taxonomía pública distingue familias por objeto real. Material, color, capacidad, Bluetooth/TWS, bambú, metal, plástico, sublimación, temporadas y campañas no generan automáticamente nuevas familias ni URLs SEO.
