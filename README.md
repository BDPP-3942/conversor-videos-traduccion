# Video Translation Pipeline

Pipeline de procesamiento multimedia para:

1. Recoger ZIP desde una carpeta local, Google Drive o rclone.
2. Extraer ZIP de forma segura, incluidos ZIP anidados.
3. Detectar MP4, MP3, WMV, MOV, MKV y AVI sin asumir una extensión única.
4. Normalizar cada entrada a MP4 + MP3.
5. Generar transcripción original con Whisper.
6. Guardar la transcripción original como VTT independiente.
7. Traducir los segmentos y generar el VTT traducido.
8. Publicar los resultados en el proveedor seleccionado.
9. Marcar automáticamente los nombres que requieren revisión.

## Arquitectura

El pipeline no depende de un proveedor concreto. Utiliza `StorageProvider` con tres implementaciones:

- `LocalStorageProvider`: el modo recomendado para desarrollo y para equipos sin nube.
- `GoogleDriveStorageProvider`: Google Drive API + OAuth de usuario.
- `RcloneStorageProvider`: adaptador opcional de compatibilidad.

Para añadir un futuro proveedor solo hay que implementar `StorageProvider` y registrarlo en la factoría; el pipeline de vídeo no se modifica.

## Estructura local

La primera ejecución crea automáticamente:

```text
storage/
├── input/                    # PON AQUÍ LOS ZIP QUE QUIERES PROCESAR
├── output/                   # MP4, MP3, VTT traducidos y manifiestos
├── original_transcriptions/  # VTT originales de Whisper
├── failures/                 # Errores por vídeo
├── archive/                  # ZIP procesados correctamente
├── work/                     # Temporales de una ejecución
├── logs/                     # pipeline.log
└── state/                    # reservado para estado futuro
```

En modo local el usuario solo necesita copiar los ZIP a `storage/input` y ejecutar el programa.

Los ZIP procesados completamente se mueven a `storage/archive/<timestamp>/` para que una tarea programada no vuelva a cogerlos. Los ZIP con errores parciales permanecen en `storage/input` para poder reintentarlos.

## Salidas

Por vídeo:

```text
37x02_OPT_DE_TAICH_LA_GRAN_RUEDA.mp4
37x02_OPT_DE_TAICH_LA_GRAN_RUEDA.mp3
37x02_OPT_DE_TAICH_LA_GRAN_RUEDA_en.vtt
```

y en la carpeta independiente:

```text
storage/original_transcriptions/
└── 37x02_OPT_DE_TAICH_LA_GRAN_RUEDA_original.vtt
```

Cuando el árbol de origen no aporta suficiente información se usan `SIN_CURSO` y/o `SIN_LECCION` y el manifiesto incluye `review_required=true`.

## Configuración que debes administrar

### `config/app.toml`

Es el fichero principal que puedes editar.

Para trabajar solo en local no necesitas cambiar nada: el valor inicial es:

```toml
[app]
provider = "local"
source = "local://storage/input"
target = "local://storage/output"
source_lang = "es"
target_lang = "en"
```

Puedes cambiar el modelo Whisper, idiomas, límites ZIP y parámetros FFmpeg en las secciones `[processing]` y `[ffmpeg]`.

### Google Drive

Rellena únicamente:

```toml
[app]
provider = "google_drive"

[google_drive]
source_folder_id = "ID_DE_INPUT"
target_folder_id = "ID_DE_OUTPUT"
credentials_file = "secrets/google/credentials.json"
token_file = "secrets/google/token.json"
```

`credentials.json` es el OAuth Client ID de tipo Desktop App descargado de Google Cloud. `token.json` se crea tras la primera autorización y contiene credenciales sensibles; ambos están excluidos del control de versiones.

Google documenta actualmente este flujo para aplicaciones de escritorio Python: se utiliza un cliente OAuth de tipo Desktop y el fichero de token se reutiliza en las ejecuciones siguientes; el access token puede renovarse con el refresh token sin repetir la autorización.

### rclone

Solo si necesitas conservar este proveedor:

```toml
[rclone]
remote = "remote_drive"
config_file = "config/rclone.conf"
```

Crea el fichero real con `rclone config` y no lo versionará Git.

## Instalación local

### Windows

```cmd
scripts\setup_env.bat
```

### Linux/macOS

```bash
./scripts/setup_env.sh
```

FFmpeg y FFprobe deben estar disponibles en `PATH`, o puedes configurar sus rutas en `[ffmpeg]`.

## Probar en local

1. Copia uno o varios ZIP a `storage/input`.
2. Ejecuta:

```cmd
scripts\run_local.bat
```

o:

```bash
./scripts/run_local.sh
```

La ejecución no necesita credenciales de nube.

También puedes comprobar el entorno con:

```bash
python main.py doctor
```

## Google Drive sin interfaz durante el trabajo

La autorización de usuario de Google se hace una sola vez en una máquina interactiva:

```bash
python main.py auth google
```

El proceso crea `secrets/google/token.json`. A partir de ese momento, `python main.py run` no inicia una autorización interactiva: utiliza el token guardado y lo refresca cuando sea necesario.

Para un equipo estrictamente sin interfaz desde el principio, realiza el comando `auth google` en otro equipo controlado, y copia `credentials.json` + `token.json` al directorio `secrets/google/` del equipo que ejecutará la tarea. El token debe tratarse como un secreto y no incrustarse en el ejecutable.

### Importante sobre Google OAuth en producción

Si la pantalla de consentimiento está configurada como aplicación externa en estado `Testing`, Google indica actualmente que los refresh tokens emitidos para esos usuarios de prueba pueden caducar a los 7 días. Para una rutina programada estable hay que revisar el estado de publicación de la aplicación y pasar a `In production` según las condiciones de Google.

## Ejecución programada

### Windows Task Scheduler

Usa `scripts\run_scheduled.bat` como acción. No contiene `pause` ni entrada interactiva.

Ejemplo conceptual:

```text
Program/script: C:\ruta\proyecto\scripts\run_scheduled.bat
Start in:       C:\ruta\proyecto
```

Configura el usuario de la tarea con permisos de lectura/escritura en `storage` y acceso a `secrets/google/token.json` si usas Drive.

### Linux cron/systemd timer

Usa:

```bash
/path/proyecto/scripts/run_scheduled.sh
```

El proceso devuelve:

```text
0 = procesamiento correcto
1 = error fatal
2 = procesamiento parcial
```

Esto permite que el programador detecte fallos sin interpretar logs.

## Ejecutable

Se recomienda `PyInstaller --onedir` en vez de `--onefile` para este proyecto porque Whisper, FFmpeg y sus modelos/binaries tienen un tamaño significativo y el formato `onedir` facilita mantener ficheros externos de configuración y secretos.

Windows:

```cmd
scripts\setup_env.bat
scripts\build_windows.bat
```

Linux:

```bash
./scripts/setup_env.sh
./scripts/build_linux.sh
```

El ejecutable se genera bajo `dist/VideoTranslationPipeline/`.

No debes incrustar `secrets/google` dentro del ejecutable. Mantén `storage/`, `config/app.toml`, `secrets/google/` y FFmpeg como datos externos al binario.

También conviene disponer el modelo Whisper de forma controlada en el equipo final; si quieres evitar descargas durante una tarea programada, predescárgalo y define la caché/modelo según tu estrategia de despliegue.

## Tests

```bash
python -m pytest
python -m ruff check .
```

Las pruebas unitarias no necesitan Google Drive. Las pruebas multimedia reales requieren FFmpeg y el resto de dependencias del entorno.
