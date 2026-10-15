# QA del dataset — 15-10-2026

- Catálogo vigente: 1.309 productos activos, 1.309 IDs y URLs únicas.
- Taxonomía: 51 familias, cero productos sin clasificar.
- Hubs: 12 productos editoriales activos por hub; intersección cero; 51 familias enlazadas.
- Sitemap distribuido: igualdad exacta con el catálogo, cero ausencias, sobrantes o duplicados.
- Sitemap del dominio: 1.396 URLs únicas; cobertura exacta de 1.309/1.309 productos.
- Los cuatro grupos históricos DUP-1 a DUP-4 siguen resueltos.
- Cuatro copias adicionales se desactivaron con redirección 301 al producto conservado: 30→356, 418→539, 1396→1292, 1430→1302. No se eliminaron productos.
- Las 51 familias y seis intenciones temáticas tienen destino de navegación; no implica activación de Ads ni una landing exclusiva para cada familia.

## Comprobaciones reproducibles sin red

```sh
python3 scripts/validate_dataset.py
python3 scripts/validate_url_ecosystem.py
python3 scripts/validate_ads_mapping.py
python3 scripts/validate_seo_hubs.py
python3 scripts/validate_sitemap.py
python3 -m unittest discover -s tests -p test_seo_integrity.py
```

## Límites abiertos

Persisten diez asociaciones a productos inexistentes en PrestaShop, que la API no permite retirar. El rastreo HTTP completo se interrumpió por respuestas 508 del hosting; no se certifica indexabilidad de todas las fichas. El nuevo sitemap fue aceptado por GSC y su procesamiento depende de Google.

Evidencia, respaldos y detalle: `reports/seo/seo_followup_20261015.md`.
