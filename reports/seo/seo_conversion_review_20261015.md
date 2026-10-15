# SEO y conversión después del rediseño — 15 de octubre de 2026

## PASS — correcciones aplicadas

- 1.309/1.309 fichas activas con dos enlaces visibles de cotización: WhatsApp y correo. Cada enlace incluye nombre, referencia y URL canónica del producto; no requiere registro. Texto de 15 px, objetivo mínimo de 44 px y ancho adaptable. Implementación: tools/repair_quote_entrypoints_20261015.py.
- Se retiraron 1.004 párrafos comerciales idénticos salvo el nombre: 924 + 80 operaciones protegidas. Se conservaron las listas de especificaciones de las 1.309 fichas. No se deduplicaron ni desactivaron más productos por similitud textual.
- Verificación completa en MariaDB: 1.309 bloques únicos, contexto correcto en ambos enlaces, cero errores, 1.004 aperturas genéricas retiradas y listas técnicas intactas. reports/seo/conversion_integrity_20261015.json.
- PS_SMARTY_FORCE_COMPILE cambió de 2 (forzar compilación por petición) a 1 (comprobar cambios de plantilla). Significado contrastado con config/defines.inc.php:227–228 y config/smarty.config.inc.php:47–48 del espejo PrestaShop. Respaldo y restauración: /home/maxdaguzan/RegalosPremium_Backups/smarty_compile_20261015/. No prueba por sí solo recuperación de capacidad ni reparación de permisos.
- Tras el cambio, comprobación secuencial: portada, contacto, ambos hubs, MORRISON y mapa HTML HTTP 200; carrusel window batch=0 HTTP 200, ok=true, 13 productos y HTML. Tiempos observados de respuesta: 0,370–0,816 s. Son muestras del servidor, no Core Web Vitals ni una prueba de carga. reports/seo/conversion_frontend_qa_20261015.json.
- Fechas de modificación actualizadas por los cambios reales de contenido. Sitemap nativo regenerado a las 15:27:23 UTC: 1.396 URLs únicas, cobertura 1.309/1.309 y lastmod de los productos 2026-10-15T12:27:19-03:00. reports/seo/content_dates_20261015.json y sitemap_after_conversion_20261015.json.
- Los cinco validadores del repositorio siguen pasando. Se mantienen las cuatro consolidaciones y cero asociaciones huérfanas documentadas anteriormente.
- Respaldos privados encadenados con SQL de restauración y SHA-256: quote_context_20261015, quote_legibility_20261015, summary_boilerplate_20261015 y summary_boilerplate_remaining_20261015. Para recuperar el estado original, restaurar en orden inverso. El piloto de formulario fue revertido antes de la publicación definitiva.

## RISK — explicación de la caída con evidencia

- Había una fricción de conversión comprobada: la ficha pedía cotizar pero carecía de acceso directo; el único WhatsApp era genérico. La portada destaca una familia de bolsas y no presenta un CTA principal de cotización. La mejora visual no acredita que el visitante encuentre más fácilmente cómo contactar. Los botones de producto ya corrigen la primera fricción; no hay un experimento que cuantifique su impacto.
- GSC, períodos iguales: 19-08 a 15-09, 35 clics/2.874 impresiones; 16-09 a 13-10, 18/2.322. Clics -48,6%, impresiones -19,2%, CTR 1,218% a 0,775%; posición media 25,00 a 25,78. Hay menos tráfico orgánico y menos clics por impresión. No demuestra que todo proceda del diseño.
- Los 14 días anteriores al 30-09 y los 14 siguientes registran 9 clics cada uno. No existe evidencia de un desplome específico provocado por el cambio SEO del 30-09. El diseño tuvo varias etapas; la fecha única y una comparación causal anterior/posterior siguen sin acreditarse.
- El HTML carga GA4 G-YZYXP2761X, GTM-N2MWGJR y Statcounter únicamente con rp_cookie_consent=accepted. Los contadores actuales no equivalen a todos los visitantes. No se debe comparar una medición anterior sin consentimiento con esta sin ajustar su alcance. No se modificó el consentimiento.
- MariaDB: ps_connections y ps_guest tienen cero filas y el registro de páginas vistas está desactivado. El conteo exacto de ps_customer_thread es dos conversaciones (10 y 13 de octubre). ps_mail registra cinco correos de plantilla contact en octubre y ocho en total; no confirma recepción ni incluye WhatsApp. Estas tablas no permiten reconstruir la conversión histórica.
- ps_log contiene 12.678 errores de escritura de plantillas asociados a carrusel2, entre julio y 11-10. Ejemplo: var/cache/prod/smarty/compile/... unable to write file. Además se observó HTTP 508 al intentar el rastreo concurrente anterior. El carrusel respondió correctamente en la muestra actual. La relación causal entre esos errores, límites del hosting y caída de contactos no está demostrada.

## PENDING — indexación contrastada, no simulada

- Se completaron 763 consultas de URL Inspection: 761 productos canónicos presentes en los ZIP de exclusiones y los dos hubs. No es un rastreo de las 1.309 fichas ni la prueba en vivo de Google.
- Estado actual de Google: 8 enviadas e indexadas; 447 rastreadas sin indexar; 209 descubiertas sin indexar; 98 que Google no reconoce; 1 error histórico de servidor. Una respuesta HTTP 500 de la API de Google se reintentó una vez y quedó resuelta; no era un 500 del sitio.
- Del export crawled: 6/452 ya indexadas y 446 siguen sin indexar. Del export discovered: 2/308 indexadas, 1 rastreada sin indexar, 207 descubiertas y 98 desconocidas. Los dos hubs figuran ahora descubiertos y asociados a ambos sitemaps. Son estados de Google fechados, anteriores a las últimas modificaciones de contenido.
- El único producto canónico del export 5xx es BEPT/1088; la inspección conserva SERVER_ERROR del 11-10 aunque su ficha respondió 200 en la comprobación pública anterior. Debe confirmarse un nuevo rastreo satisfactorio.
- 178 exclusiones robots: 176 variantes con parámetros y dos rutas de cuenta; ninguna coincide exactamente con un producto canónico activo. No se desbloquearon parámetros de ordenación indiscriminadamente.
- Las coincidencias por slug de rutas antiguas son candidatos de alias; no prueban por sí mismas redirecciones completas. No se atribuye cobertura HTTP total al catálogo ni ausencia total de contenido similar.
- Evidencia por URL y respuesta: reports/seo/gsc_exclusions_current_20261015.json. Origen: los ZIP Coverage/Performance y cinco Coverage-Drilldown del 15-10 proporcionados por el usuario.

## PENDING — bloqueos de publicación y medición

- El bloque de contacto 5 del pie está actualizado en MariaDB (tel: y enlaces a cotización y ambos hubs), pero el HTML público sigue sirviendo el pie anterior desde caché. Requiere invalidar la caché de steasycontent; no se declara publicado.
- El formulario responde 200 y muestra campos y Enviar, pero el mensaje de cotización pasado por URL no se conserva. Se descartó ese acceso contextual y se publicó correo como alternativa. No se enviaron mensajes de prueba y no está acreditada la entrega extremo a extremo.
- Para reparar permisos/espacio/propietario de var/cache, invalidar caché y corregir plantillas hacen falta acceso funcional a archivos del hosting o al back office. MariaDB funciona; SSH a 138.117.148.155:22 expiró y no hay credenciales FTP utilizables disponibles. No se cambian permisos a ciegas.
- GA4 no está autenticado en el conector disponible. Faltan sesiones por canal, dispositivo y landing, eventos de contacto y fecha exacta de cada cambio para medir conversión. No se afirma una causa única ni se promete recuperación inmediata.
