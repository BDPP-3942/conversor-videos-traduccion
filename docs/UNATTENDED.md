# Ejecución desatendida

## Modelo operativo

La aplicación tiene dos fases completamente separadas:

1. **Administración/configuración**: OAuth, selección de proveedor, carpetas y perfiles.
2. **Operación**: `run --scheduled`, sin navegador, sin preguntas y sin depender de una sesión de usuario.

Una vez terminado el setup, el operador solo necesita colocar los ZIP en el origen configurado y arrancar el ejecutable o dejar actuar al Programador de tareas.

## Local

Origen:

```text
storage/input/
```

Destino:

```text
storage/output/
```

No existe OAuth. El preflight solo comprueba que las carpetas estén disponibles.

## Google Drive

### Setup único

```bash
python main.py provider setup-google \
  --profile default \
  --source-folder-id ID_ENTRADA \
  --target-folder-id ID_SALIDA \
  --archive-folder-id ID_ARCHIVO
```

El navegador se abre únicamente en este comando.

Queda persistido:

```text
secrets/providers/google/default/credentials.json
secrets/providers/google/default/token.json
config/runtime.toml
```

El `token.json` contiene el refresh token cuando Google lo proporciona. En cada ejecución desatendida el preflight hace una comprobación silenciosa:

- si el access token sigue siendo válido, continúa;
- si ha caducado y existe refresh token, lo renueva automáticamente y vuelve a guardar `token.json`;
- si el refresh token ya no es válido, **no intenta abrir el navegador** y termina como `not_ready`.

También se puede comprobar manualmente:

```bash
python main.py provider verify google_drive --profile default
```

La verificación no inicia nunca el consentimiento interactivo.

## rclone

### Setup único

```bash
python main.py provider setup-rclone dropbox_main dropbox \
  --source input \
  --target output
```

El binario se guarda de forma privada en:

```text
tools/rclone/
```

y el fichero de configuración en:

```text
secrets/rclone/rclone.conf
```

No se necesita una instalación global de rclone.

### OAuth y refresh

rclone es quien gestiona el token OAuth del backend. En cada ejecución desatendida el pipeline ejecuta un **healthcheck de solo lectura** sobre la carpeta de entrada. Esa llamada obliga a rclone a usar el remoto; cuando el backend soporta refresh OAuth, rclone puede renovar el access token y persistir la nueva credencial en `rclone.conf`.

No se inicia un asistente ni se solicita interacción en ese proceso.

La comprobación manual es:

```bash
python main.py provider verify rclone --profile dropbox_main --location input
```

Si el proveedor requiere reautorización, el healthcheck falla y el scheduler registra `not_ready`. Entonces se ejecuta de nuevo el setup interactivo para ese remoto.

### Varios proveedores

Todos los remotos pueden coexistir:

```text
rclone.conf
├── dropbox_main
├── onedrive_main
├── google_cloud
└── s3_backup
```

Cambiar de proveedor no elimina el anterior:

```bash
python main.py provider setup-rclone onedrive_main onedrive --source input --target output
python main.py provider use rclone --profile onedrive_main --source rclone://input --target rclone://output
```

Para volver:

```bash
python main.py provider use rclone --profile dropbox_main --source rclone://input --target rclone://output
```

El remoto anterior sigue configurado y autorizado.

## Actualización automática de rclone

Por defecto está **desactivada** para que una tarea programada no cambie su ejecutable sin una decisión administrativa.

Para habilitarla:

```toml
[runtime]
auto_update_rclone = true
```

También puede hacerse manualmente:

```bash
python main.py provider update-rclone --force
```

rclone documenta `selfupdate --check` para consultar una versión nueva y `selfupdate` para instalar la última estable, verificando la descarga.

## Ejecutable portable

El directorio que contiene `VideoTranslationPipeline.exe` es la raíz operativa. No se almacenan tokens dentro del bundle PyInstaller.

```text
VideoTranslationPipeline/
├── VideoTranslationPipeline.exe
├── config/
├── secrets/
├── storage/
└── tools/
```

Al arrancar por doble clic, el ejecutable no debe pedir nada. En esta versión, la ejecución sin argumentos equivale al modo desatendido.

## Reprocesado desatendido

`reprocess-subtitles` es un subcomando de primera clase del ejecutable y también puede ejecutarse desde los wrappers usados por tareas programadas. En modo `--scheduled` utiliza el proveedor/target persistidos y no solicita interacción.

Ejemplos:

```text
VideoTranslationPipeline.exe reprocess-subtitles --scheduled --output-folder 37x02_Tema --stt-only
VideoTranslationPipeline.exe reprocess-subtitles --scheduled --output-folder 37x02_Tema --translate-only
```

Con los wrappers:

```bash
./scripts/run_unattended.sh reprocess-subtitles --output-folder 37x02_Tema --stt-only
./scripts/reprocess_subtitles.sh --scheduled --output-folder 37x02_Tema --translate-only
```

El instalador de tareas de Windows acepta una cadena de argumentos mediante `-Arguments`, por lo que una tarea puede ejecutar `run --scheduled` o cualquier modo de reprocesado soportado.

## Programador de tareas de Windows

Usar:

```text
VideoTranslationPipeline.exe run --scheduled
```

Directorio de inicio:

```text
<carpeta del ejecutable>
```

La tarea debe utilizar la **misma cuenta de Windows que realizó el setup OAuth** o una cuenta que tenga acceso equivalente a `secrets/`, `storage/` y `tools/`.

Recomendaciones:

- `Run whether user is logged on or not`.
- Privilegios mínimos; no requiere administrador.
- No ejecutar una segunda instancia simultánea.
- Mantener el paquete en una ruta estable y con permisos de escritura para `secrets/`, `storage/` y `tools/`.
- Usar `scripts/install_task_scheduler.ps1` para crear la tarea con el directorio de trabajo correcto.

## Linux

Con cron:

```cron
*/5 * * * * cd /opt/video-translation-pipeline && ./VideoTranslationPipeline run --scheduled >> storage/logs/scheduler.log 2>&1
```

Con systemd se recomienda un usuario de servicio dedicado que sea propietario de `secrets/` y haya ejecutado la autorización inicial.

## Regeneración limpia desde wrappers locales

La operación de regeneración limpia ya existente se publica como `video-translation-regenerate` y se implementa en `src.regeneration`. Los wrappers locales `run_local.sh` y `run_local.bat` pueden despacharla mediante `regenerate`; no contienen lógica de regeneración propia.

```bash
./scripts/run_local.sh regenerate --config config/app.toml
```

En Windows:

```text
scripts\run_local.bat regenerate --config config\app.toml
```

Ambos comandos utilizan la misma implementación que el entry point de regeneración: `MediaPipeline` y el contrato público `StorageProvider` siguen siendo responsables del procesamiento, backup, rollback y cleanup.

## Ciclo completo

```text
CONFIGURACIÓN ÚNICA
    ├─ Google OAuth → token.json
    ├─ rclone remote + OAuth → rclone.conf
    └─ selección de proveedor + carpetas → runtime.toml
              ↓
PREPARACIÓN DESATENDIDA
    ├─ Google: refresh silencioso cuando procede
    └─ rclone: healthcheck de solo lectura → refresh del backend cuando procede
              ↓
SCHEDULER / BOTÓN INICIAR
              ↓
leer ZIP de input
              ↓
procesar
              ↓
escribir/subir salida
              ↓
archivar origen
              ↓
finalizar
```
