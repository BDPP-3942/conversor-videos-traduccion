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

El `token.json` contiene el refresh token cuando Google lo proporciona. En cada ejecución desatendida el preflight hace una comprobación silenciosa.

También se puede comprobar manualmente:

```bash
python main.py provider verify google_drive --profile default
```

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

### Varios proveedores

Todos los remotos pueden coexistir y el proveedor activo queda persistido mediante `provider use`.

## Actualización automática de rclone

Por defecto está desactivada para que una tarea programada no cambie su ejecutable sin una decisión administrativa.

## Ejecutable portable

El directorio que contiene `VideoTranslationPipeline.exe` es la raíz operativa. No se almacenan tokens dentro del bundle PyInstaller.

## Reprocesado desatendido

`reprocess-subtitles` es un subcomando de primera clase del ejecutable y también puede ejecutarse desde los wrappers usados por tareas programadas.

## Regeneración limpia

La regeneración limpia es una operación de primera clase implementada en `src.regeneration` y publicada como `video-translation-regenerate`. Los scripts no contienen una implementación alternativa.

Desde un entorno local preparado se puede ejecutar mediante el wrapper:

```bash
./scripts/run_local.sh regenerate --config config/app.toml
```

En Windows:

```text
scripts\run_local.bat regenerate --config config\app.toml
```

Ambos wrappers solo seleccionan el módulo existente `src.regeneration`; el backup, rollback, storage y `MediaPipeline` siguen perteneciendo a la implementación común.
