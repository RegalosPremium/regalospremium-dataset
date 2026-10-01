# Google Ads CLI con service account

## Alcance y seguridad

Este flujo prepara acceso no interactivo para el proyecto Cloud existente `regalospremium-ads-api`. No usa ni lee el client secret Desktop App, passkeys, refresh tokens ni OAuth interactivo. Una service account debe ser agregada como usuario de la cuenta Google Ads `592-182-2090` (o de su MCC) y requiere un developer token válido. Google recomienda tratar tanto el developer token como el JSON de la service account como contraseñas.

No hay ningún secreto en este repositorio. La plantilla versionada es `config/google-ads.example.yaml`; el archivo real y la clave viven fuera del repo con permisos de dueño únicamente.

## Pasos externos restantes

1. En el proyecto Cloud `regalospremium-ads-api`, cree o ubique una clave JSON de la service account autorizada. Guárdela fuera del repositorio y obtenga su `client_email` desde ese JSON.

2. Cree el directorio privado, instale el JSON y limite sus permisos:

   ```bash
   install -d -m 700 ~/.config/regalospremium
   install -m 600 /RUTA/SEGURA/service-account.json ~/.config/regalospremium/service-account.json
   chmod 600 ~/.config/regalospremium/service-account.json
   ```

3. En Google Ads, agregue ese `client_email` como usuario de la cuenta cliente `592-182-2090` (o del MCC que la administra), con el mínimo permiso de solo lectura necesario. Si se usa MCC, conserve su ID para `login_customer_id`.

4. Obtenga el `developer_token` autorizado para la API de Google Ads. No lo guarde en el repositorio.

5. Prepare el entorno local e instale las dependencias:

   ```bash
   python3 -m venv .venv-ads
   .venv-ads/bin/python -m pip install --upgrade pip
   .venv-ads/bin/pip install -r requirements-ads.txt
   ```

6. Cree la configuración privada y edítela localmente, sin pegar secretos en el repo:

   ```bash
   cp config/google-ads.example.yaml ~/.config/regalospremium/google-ads.yaml
   chmod 600 ~/.config/regalospremium/google-ads.yaml
   ```

```yaml
developer_token: SU_DEVELOPER_TOKEN
json_key_file_path: /home/USUARIO/.config/regalospremium/service-account.json
customer_id: "5921822090"
# login_customer_id: "MCC_SI_CORRESPONDE"
use_proto_plus: true
```

Si se usa un MCC, `login_customer_id` es el ID del MCC, no el cliente final. El JSON y el YAML deben conservar `chmod 600`.

## Flujo seguro

7. Verificar acceso de lectura, sin mutaciones:

   ```bash
   .venv-ads/bin/python scripts/ads_readonly_check.py
   ```

   Valida forma/permisos de la clave, llama `listAccessibleCustomers` y lista campañas no eliminadas de `5921822090` mediante GAQL. No invoca ningún servicio `mutate`.

8. Justo antes de una futura escritura, guardar un snapshot local (ruta ignorada por Git):

   ```bash
   .venv-ads/bin/python scripts/ads_snapshot.py --output reports/ads/live/prewrite-$(date +%Y%m%d-%H%M%S).json
   ```

   Incluye campañas, ad groups, ads y keywords, todos por consultas de lectura. El JSON permite comparar/restaurar manualmente los valores previos; no ejecuta rollback automático.

9. Validar el plan de los CSV sin red ni API (su reporte también queda ignorado):

   ```bash
   .venv-ads/bin/python scripts/ads_generic_dry_run.py --output reports/ads/generic-dry-run.json
   ```

   El plan declara `mutations_sent: 0`. No tiene `--apply`: faltan decisiones de campaña/presupuesto/puja/segmentación y la aprobación explícita antes de escribir.

## Pendientes externos

- `developer_token` de Google Ads API.
- Service account creada en `regalospremium-ads-api`, clave JSON nueva y guardada fuera del repo.
- Invitar el email de esa service account a la cuenta `592-182-2090` o al MCC correspondiente, y confirmar si se requiere `login_customer_id`.
- Antes de cualquier futura implementación: aprobar campaña objetivo o creación, presupuesto, puja, red, ubicación, idioma y exclusiones DSA; ejecutar y revisar el snapshot.
