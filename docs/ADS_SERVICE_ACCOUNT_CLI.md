# Google Ads CLI con service account impersonada

## Ruta vigente: keyless impersonation

La organización de Google Cloud bloquea la creación de claves JSON de service account. La ruta vigente es, por tanto, **Service Account Impersonation**: `ventas@regalospremium.cl` obtiene credenciales de corta duración para `rp-google-ads-cli@regalospremium-ads-api.iam.gserviceaccount.com` mediante IAM Credentials API, con el scope `https://www.googleapis.com/auth/adwords`.

El token OAuth Cloud local es privado y nunca debe versionarse, imprimirse ni pegarse en comandos. Este repositorio no lee secretos para validarlos: sólo comprueba que el archivo exista y tenga `chmod 600`; la librería de Google lo consume internamente al crear las credenciales. El developer token también es secreto y no se muestra en ninguna salida.

La IAM Credentials API debe permanecer habilitada y `ventas@regalospremium.cl` debe mantener `roles/iam.serviceAccountTokenCreator` sobre la service account destino. Además, esa identidad debe disponer de acceso de sólo lectura a Google Ads `592-182-2090`, o al MCC correspondiente.

## Configuración privada

Prepare el directorio una vez y conserve permisos restrictivos:

```bash
install -d -m 700 ~/.config/regalospremium
cp config/google-ads.example.yaml ~/.config/regalospremium/google-ads.yaml
chmod 600 ~/.config/regalospremium/google-ads.yaml
chmod 600 ~/.config/regalospremium/gcp-user-token.json
```

Complete sólo `developer_token` en el YAML local. La configuración keyless vigente es:

```yaml
auth_mode: impersonated_service_account
target_service_account: rp-google-ads-cli@regalospremium-ads-api.iam.gserviceaccount.com
source_user_token_path: /home/USUARIO/.config/regalospremium/gcp-user-token.json
developer_token: SU_DEVELOPER_TOKEN
customer_id: "5921822090"
# login_customer_id: "MCC_SI_CORRESPONDE"
use_proto_plus: true
```

`login_customer_id`, si existe, es el ID del MCC, no el cliente final. No añada `client_id`, `client_secret` ni `refresh_token` al YAML.

El modo heredado `service_account_json` se conserva sólo como fallback para instalaciones que ya cuenten con una JSON key permitida. En esta organización no es la ruta soportada ni debe intentarse crear una clave para usarlo.

## Entorno y operaciones de sólo lectura

Instale las dependencias únicamente cuando sea necesario:

```bash
python3 -m venv .venv-ads
.venv-ads/bin/python -m pip install --upgrade pip
.venv-ads/bin/pip install -r requirements-ads.txt
```

Verifique acceso sin mutaciones:

```bash
.venv-ads/bin/python scripts/ads_readonly_check.py
```

El comando valida localmente el modo y permisos del token, solicita credenciales impersonadas y sólo ejecuta `listAccessibleCustomers` y una consulta GAQL de campañas. No llama servicios `mutate` y nunca imprime access tokens ni refresh tokens.

Antes de una futura escritura autorizada, cree un snapshot local ignorado por Git:

```bash
.venv-ads/bin/python scripts/ads_snapshot.py --output reports/ads/live/prewrite-$(date +%Y%m%d-%H%M%S).json
```

También puede validar los CSV sin red:

```bash
.venv-ads/bin/python scripts/ads_generic_dry_run.py --output reports/ads/generic-dry-run.json
```

No hay `--apply`: cualquier escritura posterior requiere decisión explícita sobre campaña, presupuesto, puja, red, ubicación, idioma y exclusiones DSA.
