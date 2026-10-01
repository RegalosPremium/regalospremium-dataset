# Google Ads CLI con service account impersonada

## Ruta vigente: gcloud keyless + proyecto Explorer

La integración productiva usa **Google Cloud CLI oficial** y credenciales temporales impersonadas. No se usa JSON key ni refresh token manual.

Proyecto Google Cloud con acceso Google Ads **Explorer**:

- project_id: `able-marking-493221-m5`
- project_number: `234610997699`
- service account: `rp-google-ads-cli@able-marking-493221-m5.iam.gserviceaccount.com`
- usuario gcloud propietario: `max.daguzan@gmail.com`
- cuenta Google Ads: `592-182-2090`

La service account está agregada a Google Ads con nivel **Estándar** y `max.daguzan@gmail.com` tiene `roles/iam.serviceAccountTokenCreator` sobre esa service account. La IAM Credentials API y Google Ads API están habilitadas en el proyecto Explorer.

La service account anterior `rp-google-ads-cli@regalospremium-ads-api.iam.gserviceaccount.com` queda como legado/rollback y no debe usarse para producción porque su proyecto sólo tenía acceso de prueba.

Desde el 2026-09-09 Google Ads no requiere developer token. Con `google-ads` 33.0.0 el campo es opcional.

## Instalación de gcloud

Google Cloud CLI está instalado sólo para el usuario local:

```bash
/home/maxdaguzan/.local/gcloud-install/google-cloud-sdk/bin/gcloud
```

La configuración aislada usada para Ads es:

```bash
~/.config/gcloud-rp-explorer
```

Compruebe la identidad activa:

```bash
CLOUDSDK_CONFIG=~/.config/gcloud-rp-explorer ~/.local/gcloud-install/google-cloud-sdk/bin/gcloud auth list
```

## Configuración privada

```yaml
auth_mode: gcloud_impersonation
target_service_account: rp-google-ads-cli@able-marking-493221-m5.iam.gserviceaccount.com
gcloud_path: /home/USUARIO/.local/gcloud-install/google-cloud-sdk/bin/gcloud
gcloud_config_dir: /home/USUARIO/.config/gcloud-rp-explorer
customer_id: "5921822090"
use_proto_plus: true
```

El archivo real vive en:

```bash
~/.config/regalospremium/google-ads.yaml
```

y debe conservar `chmod 600`.

## Entorno Python

```bash
python3 -m venv .venv-ads
.venv-ads/bin/pip install -r requirements-ads.txt
```

Versión validada: `google-ads==33.0.0`.

## QA de sólo lectura

```bash
.venv-ads/bin/python scripts/ads_readonly_check.py
```

El probe productivo validado devuelve acceso a `5921822090` mediante `gcloud_impersonation`.

Antes de cualquier mutación:

```bash
.venv-ads/bin/python scripts/ads_snapshot.py   --output reports/ads/live/prewrite-$(date +%Y%m%d-%H%M%S).json
```

## Cambios B2B aplicados

La campaña `23529944814 / Regalos Premium B2B` permanece **PAUSED**.

- `scripts/ads_apply_generic_b2b.py`: completa las 24 keywords prioritarias exacta/frase y actualiza el RSA genérico a 15 titulares + 4 descripciones.
- `scripts/ads_apply_dsa_b2b.py`: habilita DSA en la campaña y crea el grupo `DSA | Canonicales B2B`, también **PAUSED**, con siete targets canónicos.
- La home no se usa como target DSA para evitar que un criterio URL raíz abarque todo el dominio.
- La campaña no debe activarse hasta cerrar QA comercial, exclusiones y estado de facturación.

## Rollback y seguridad

Los snapshots `reports/ads/live/prewrite-*.json` y `post-*.json` permiten comparar el estado antes/después. No se almacenan access tokens, refresh tokens, client secrets ni JSON keys en Git.
