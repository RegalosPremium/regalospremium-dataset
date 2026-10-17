# Base de componentes y patrones reutilizables probados

Actualizado: 2026-10-16

## Objetivo

Mantener una base de ingeniería reutilizable para Regalos Premium y RPCH. Antes de desarrollar una capacidad nueva, se debe comprobar si existe un componente o patrón probado que pueda adaptarse.

Regla: **buscar → estudiar → aislar → probar → adaptar → integrar**.

No se copia código por similitud. Se reutilizan contratos, patrones o componentes sólo después de entender ownership, dependencias, lifecycle, licencia y evidencia de pruebas.

---

# 1. Ojo de Dios / gods-eye-view

Fuente local:

`/home/maxdaguzan/Descargas/gods-eye-view`

Repositorio upstream:

`bilawalsidhu/gods-eye-view`

Licencia: MIT.

Baseline analizado:

`e7707d9a0f34d9fbffc300023c319f95caa5be30`

Versión package: `0.1.1`.

## Principios arquitectónicos adoptados

- ownership explícito por componente;
- import/package boundaries verificables;
- contratos portables;
- dependencias inyectadas;
- construcción/importación sin efectos laterales;
- lifecycle explícito y destrucción determinista;
- cancelación de trabajos asíncronos;
- separación source / provider / renderer / composition;
- estado propiedad del componente, no del import;
- acceptance gates independientes;
- QA como evidencia, no como formalidad;
- validar el candidato integrado antes de promoverlo;
- separar componentes reutilizables de composición standalone.

## Evidencia local dirigida

Después de instalar exactamente las dependencias del lockfile mediante `npm ci`, se ejecutó:

```text
node --test   src/app/sourceSlot.test.mjs   src/app/stateChannel.test.mjs   src/services/requests.test.mjs   src/layers/cctv/source.test.mjs
```

Resultado:

```text
tests 18
pass 18
fail 0
cancelled 0
skipped 0
EXIT 0
```

Por lo tanto, los componentes/patrones de esta sección se clasifican como **VERIFIED_LOCAL** para el baseline indicado.

### 1.1 createSourceSlot — VERIFIED_LOCAL

Ruta:
`src/sources/sourceSlot.js`

Uso reutilizable:
- intercambio de proveedor sin reemplazar al consumidor;
- validación de contrato al configurar;
- métodos opcionales con fallback explícito;
- rechazo de resultados asíncronos de un proveedor reemplazado;
- cleanup antiguo incapaz de desmontar un provider nuevo.

Aplicaciones RP:
- proveedor de stock StockSur/CDO;
- proveedor de catálogo;
- backend WhatsApp;
- fuentes intercambiables de disponibilidad;
- APIs primarias/fallback.

### 1.2 createStateChannel — VERIFIED_LOCAL

Ruta:
`src/app/stateChannel.js`

Uso reutilizable:
- snapshots inmutables;
- copia profunda de datos planos;
- revisiones ordenadas;
- publicación reentrante sin desorden;
- suscripción con estado actual;
- aislamiento ante excepción de un consumidor;
- destroy() que revoca listeners y cola pendiente.

Aplicaciones RP:
- estado del cotizador;
- selección de productos;
- stock consultado;
- estados de WhatsApp;
- estado UI compartido entre componentes.

### 1.3 createApplicationRequestServices — VERIFIED_LOCAL

Ruta:
`src/services/requests.js`

Uso reutilizable:
- `fetchImpl` inyectable;
- AbortSignal de lifecycle + señal por operación;
- cancelación de respuestas tardías;
- redirect explícito;
- capability probe acotado;
- timeout/backoff;
- Retry-After;
- validación de entrada;
- servicios independientes.

Aplicaciones RP:
- stock;
- proveedores;
- cotizador;
- WhatsApp;
- APIs WooCommerce/PrestaShop;
- servicios con fallback y rate limits.

### 1.4 Source/lifecycle de CCTV — VERIFIED_LOCAL como patrón

Prueba dirigida:
`src/layers/cctv/source.test.mjs`

Patrones validados:
- construcción inerte;
- adquisición sólo al iniciar;
- AbortController por lifecycle;
- destroy cancela adquisición pendiente;
- respuesta tardía no publica estado;
- encoding estable de identidad;
- snapshots malformados fallan explícitamente.

No se reutiliza la lógica CCTV/Cesium en RP. Se reutiliza el patrón de ownership y lifecycle.

---

# 2. Ojo de Dios — patrones revisados que requieren prueba dirigida antes de portar

Estado: **REVIEWED_ARCHITECTURE**.

### 2.1 Capped HTTP body

Ruta:
`src/sources/httpBody.js`

Funciones:
- `readResponseTextCapped`
- `readResponseJsonCapped`
- `readResponseBytesCapped`
- `coalesceProxyRequest`

Valor:
- límite duro de bytes;
- rechazo temprano por Content-Length;
- límite durante streaming;
- cancelación con AbortSignal;
- coalescing de peticiones idénticas en vuelo.

Uso probable:
- APIs de proveedores;
- descargas de catálogos;
- imágenes/metadatos;
- protección contra respuestas anómalas.

### 2.2 Rate limiter acotado

Ruta:
`src/sources/rateLimit.js`

Función:
`makeRateLimiter({ windowMs, max, globalMax })`

Valor:
- cuota por clave;
- backstop global;
- límite duro de claves;
- limpieza de entradas antiguas.

Uso probable:
- consulta stock;
- endpoints de cotización;
- WhatsApp;
- proxies costosos.

### 2.3 Request body cap

Ruta:
`server/providers/common/request.js`

Valor:
- evita bodies sin límite;
- código de error estructurado `BODY_TOO_LARGE`;
- drena la petición sin retener bytes tras superar el máximo.

Uso probable:
- webhook WhatsApp;
- formularios;
- APIs internas.

---

# 3. Boundary gates del Ojo de Dios

Comando:

`npm run check:boundaries`

La primera fase reportó:

```json
{"modules":834,"portableEntries":66}
```

La validación completa seguía ejecutándose durante el levantamiento de esta base, por lo que **no se marca aún como PASS completo**.

Regla adoptada:
- ningún componente reusable debe importar composición standalone;
- browser no debe alcanzar Node/server/test;
- sources portables no deben depender de renderer/app/server;
- providers no deben importar rendering;
- package exports son inventario autoritativo;
- imports deben ser explícitos y auditables.

---

# 4. Activos internos maduros

## 4.1 Cargador PrestaShop — PROBADO / REUTILIZAR

Ruta:
`/home/maxdaguzan/Descargas/Creador_Plantillas_v1.1/creador-plantillas-app/cargador_prestashop.py`

Capacidades observadas:
- credenciales;
- journal;
- request y errores;
- blank schema;
- validación SEO;
- validación de archivos;
- búsqueda de producto;
- tags;
- asociaciones;
- creación;
- upload de imágenes;
- conversión WebP→JPEG;
- activación;
- actualización;
- snapshot;
- rollback.

Regla:
**usar mediante bridge estable. No reescribir el write-path.**

## 4.2 Contratos del RP Ingest Engine — REUTILIZAR

Ruta:
`/home/maxdaguzan/rp-ingest-engine/src/app/contracts.py`

Contratos:
- `CatalogSource`
- `ArtifactBuilder`
- `CatalogSink`
- `EvidenceSink`

Valor:
interfaces pequeñas, ownership claro y posibilidad de cambiar source/sink sin contaminar dominio.

## 4.3 Modelos de dominio del RP Ingest Engine — REUTILIZAR

Ruta:
`/home/maxdaguzan/rp-ingest-engine/src/domain/models.py`

Modelos:
- `SourceProduct`
- `LoadArtifact`
- `ProductResult`

Valor:
datos explícitos y portables; modelos de entrada inmutables mediante dataclasses frozen.

## 4.4 Circuit breaker — REUTILIZAR

Ruta:
`/home/maxdaguzan/rp-ingest-engine/src/services/circuit_breaker.py`

Patrón:
- firma estructural del error;
- normaliza números;
- cuenta fallos equivalentes;
- abre por defecto en 3 repeticiones;
- apertura inmediata para condiciones graves.

Uso:
- ingestas;
- consulta stock;
- conectores;
- WhatsApp;
- cotización;
- operaciones masivas.

---

# 5. Componentes funcionales existentes que deben evaluarse antes de crear otros

- consulta de stock / conectores StockSur y CDO;
- Cotizador Regalos Premium;
- integración WhatsApp y supervisor;
- motores de ingesta;
- cargador PrestaShop;
- validadores SEO y de catálogo;
- QA y circuit breaker.

Regla LA-0003: **no reinventar una capacidad que ya existe sin demostrar primero por qué el componente existente no satisface el contrato nuevo**.

---

# 6. Clasificación de reutilización

| Estado | Significado |
|---|---|
| VERIFIED_LOCAL | Código/patrón ejecutado localmente con prueba dirigida PASS |
| PROBADO / REUTILIZAR | Activo interno con historial operativo y contrato definido |
| REVIEWED_ARCHITECTURE | Diseño revisado; requiere prueba específica antes de portar |
| ADAPTAR | Útil, pero necesita wrapper/bridge o cambio de contrato |
| NO TRANSPLANTAR | Dominio específico o dependencia innecesaria |

---

# 7. No transplantar ciegamente

Del Ojo de Dios no se deben importar por defecto:
- Cesium/rendering geoespacial;
- algoritmos orbitales;
- CCTV visual;
- módulos militares;
- tránsito, clima o GIS;
- dependencias pesadas no necesarias.

La reutilización prioritaria es:
**contratos, lifecycle, cancelación, ownership, request safety, state channels, rate limits, boundary gates y QA**.

---

# 8. Regla de admisión futura

Un componente entra en esta base sólo si se registra:
1. origen y commit/version;
2. licencia;
3. propósito;
4. dependencias;
5. ownership;
6. side effects;
7. lifecycle;
8. prueba local o evidencia operacional;
9. decisión: reutilizar/adaptar/rechazar;
10. consumidores previstos.

Esta base debe consultarse antes de comenzar un nuevo bloque de programación.
