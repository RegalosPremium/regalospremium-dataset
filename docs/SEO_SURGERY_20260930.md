# SEO Surgery — 2026-09-30

## Producción
- `/publicitarios-bamboo/` → 301 → `/regalos-corporativos-bambu/`.
- Subárbol `/publicitarios-bamboo/*` consolidado al subárbol canónico nuevo.
- B47 / ID 1362 queda en cuarentena: su URL canónica devolvía 404; se retira del sitemap y se redirige temporalmente al hub Bamboo.
- `/mugs-botellas-termos/` conserva URL y canonical; se actualizan H1, title, meta description y texto B2B.

## Keywords B2B prioritarias
- regalos corporativos
- merchandising corporativo
- regalos para empresas
- merchandising empresarial

## Google Ads
Se preparan keywords exact/phrase, activos RSA y targets DSA. No se publica automáticamente mientras no exista `config/google-ads.yaml` y `GOOGLE_ADS_CUSTOMER_ID`.

## QA requerido
- Viejo Bamboo: 301 directo.
- Bamboo nuevo: 200.
- Mugs: 200 + canonical propio.
- Sitemaps: XML válido y 200.
- B47: no debe figurar en sitemap mientras siga sin renderizar.
