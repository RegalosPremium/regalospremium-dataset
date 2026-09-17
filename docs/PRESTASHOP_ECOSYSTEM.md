# PrestaShop → BBDD del ecosistema

La BBDD del ecosistema es un espejo separado de la base de producción.
PrestaShop aporta estado operativo; GitHub aporta canonical y taxonomía SEO; Google Ads aporta intención y destinos históricos.

## Fuente operativa

El poblador consulta `ps_product`, `ps_product_shop`, `ps_product_lang`, `ps_category`, `ps_category_lang` y `ps_category_product`.
No escribe en ninguna tabla de PrestaShop.

## BBDD generada

`var/ecosystem.db` es SQLite local y está excluida de Git. Se regenera completa en cada sincronización.
Contiene productos históricos/activos, categorías, relaciones, taxonomía, keywords Ads, blueprint, registro de URLs y anomalías de PrestaShop.

## Conexión

Copiar `config/prestashop-mysql.example.cnf` a `config/prestashop-mysql.cnf` y completar credenciales. El archivo real está ignorado por Git.
El script también admite `--mysql-socket` para QA local contra un dump restaurado.

## Ejecución

`python3 scripts/build_ecosystem_db.py --defaults-extra-file config/prestashop-mysql.cnf --database NOMBRE_BBDD`

Después ejecutar:

`python3 scripts/validate_ecosystem_db.py`

## Reglas

- Un producto activo de PrestaShop debe existir en `data/productos.csv`.
- El canonical de producto viene de GitHub; no se reemplaza por una URL inferida.
- Categorías borradas y relaciones huérfanas se registran en `prestashop_anomalies`.
- Las landings Ads sólo se resuelven automáticamente con evidencia dominante de PrestaShop o Ads histórico.
- La sincronización de Google Ads permanece dry-run hasta uso explícito de `--apply`.
