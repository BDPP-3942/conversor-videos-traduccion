# Conversor de traducción de vídeos

Pipeline Python multiplataforma para procesar ZIP con vídeo/audio, normalizar los medios con FFmpeg, transcribir con Whisper y generar subtítulos traducidos. Puede trabajar en local o usar Google Drive/rclone como almacenamiento remoto. El procesamiento pesado (FFmpeg, Whisper y traducción) sigue ejecutándose en el equipo local; la nube se utiliza para descargar entradas y subir resultados.

## Requisitos

- Python **3.11, 3.12 o 3.13**.
- Python 3.14 todavía no está soportado por el proyecto.
- FFmpeg no necesita estar instalado globalmente: `imageio-ffmpeg` proporciona un binario como fallback.
- Para Google Drive se necesitan credenciales OAuth y las dependencias opcionales de `requirements-google.txt`.
- Para rclone se necesita el ejecutable `rclone`; no es una librería Python necesaria para este proyecto.

## Estructura de almacenamiento

Todo el almacenamiento local queda bajo `storage/`:

```text
storage/
├── input/                         # ZIP pendientes de procesar
├── work/                          # Temporales de una ejecución; se eliminan al terminar
├── output/
│   ├── <resultado>/
│   │   ├── <resultado>.mp4
│   │   ├── <resultado>.mp3
│   │   ├── <resultado>_en.vtt
│   │   └── original_transcriptions/
│   │       └── <resultado>_original.vtt
│   └── _manifests/
├── archive/
│   └── sources/                   # ZIP procesados correctamente si se conserva el origen
├── state/
│   └── processed.jsonl            # Registro local de ZIP procesados correctamente
├── failures/                      # Errores por medio
└── logs/
```

## Preparación del entorno

### Windows

```bat
scripts\setup_env.bat
scripts\run_local.bat
```

### Linux/macOS

```bash
./scripts/setup_env.sh
./scripts/run_local.sh
```

Los scripts usan siempre `.venv`, resuelven la raíz real del proyecto aunque se ejecuten desde `scripts/` y rechazan Python fuera del rango 3.11–3.13.

## Configuración

La configuración principal está en `config/app.toml`.

También se puede crear `.env` a partir de `.env.example`. El proyecto carga `.env` automáticamente mediante `python-dotenv`; las variables de entorno tienen prioridad sobre `app.toml`.

Ejemplo:

```text
STORAGE_PROVIDER=local
SOURCE_URI=local://storage/input
TARGET_URI=local://storage/output
SOURCE_LANG=es
TARGET_LANG=en
```

## Google Drive

Para usar Google Drive:

1. Configura `source_folder_id` y `target_folder_id` en `config/app.toml` o mediante variables de entorno.
2. Coloca las credenciales OAuth en `secrets/google/credentials.json`.
3. Ejecuta una vez:

```bash
./scripts/setup_google.sh
```

En Windows:

```bat
scripts\setup_google.bat
```

El script instala `requirements-google.txt` y ejecuta la autorización interactiva. Después, el token queda en `secrets/google/token.json` y las ejecuciones programadas pueden ser desatendidas mientras el token siga siendo válido/renovable.

Los archivos de credenciales y tokens están excluidos de Git. Para ejecución programada en cloud, configura también `archive_folder_id` para mover el ZIP procesado fuera de `Input` después del éxito.

## rclone

Rclone es un **programa externo de línea de comandos**, no una librería Python de este proyecto. Es un adaptador muy útil cuando quieres soportar muchos proveedores cloud con una sola interfaz; rclone soporta más de 70 productos de almacenamiento cloud y se usa desde scripts o CLI. 

Para usarlo:

```bash
./scripts/setup_rclone.sh
rclone config
```

En Windows: `scripts\setup_rclone.bat` y después `rclone config`. El proyecto invoca `rclone` como proceso externo usando el archivo `config/rclone.conf`; no requiere instalar un paquete Python para rclone.

## Modos de ejecución

El mismo ejecutable admite dos modos principales:

- `--mode local`: usa `storage/input` y `storage/output` locales.
- `--mode cloud`: usa Google Drive como entrada/salida, descarga temporalmente al equipo, procesa localmente, sube MP4/MPEG y VTT y archiva el ZIP remoto después de un procesamiento correcto.
- `--mode rclone`: usa un remoto configurado en rclone como almacenamiento.

Ejemplos:

```bash
./scripts/run_local.sh
./scripts/run_local.sh --mode cloud
./scripts/run_local.sh --mode cloud --parallel-videos 2 --resume
./scripts/run_local.sh --mode rclone
```

`run_scheduled.sh` y `run_scheduled.bat` ejecutan por defecto el modo `cloud`; se pueden pasar argumentos adicionales o usar `--mode local` para una tarea local. La tarea programada solo lanza el ejecutable: el propio proceso realiza autenticación, descarga, procesamiento, subida, archivado y limpieza.

En modo cloud, los resultados se escriben en un directorio temporal de trabajo y se suben directamente al destino remoto; una vez destruido el `TemporaryDirectory`, los MP4/MPEG y VTT generados dejan de existir localmente. El manifest pequeño se conserva localmente para reanudación y se publica también en Google Drive. El ZIP remoto se mueve a `archive_folder_id` después del éxito, evitando que la siguiente ejecución vuelva a seleccionarlo.

## Ejecución

Local:

```bash
python main.py run --provider local
```

Google Drive manual:

```bash
python main.py run --mode cloud
```

Comprobación del entorno:

```bash
python main.py doctor
```

Inicialización de carpetas:

```bash
python main.py init
```

También se instala un entry point si se ejecuta `pip install .`:

```bash
video-translation-pipeline doctor
```

## Nombres de archivos y compatibilidad con WordPress

Los nombres de salida se normalizan a un formato ASCII estable antes de tocar el filesystem. Los acentos se transliteran (`á` → `a`, `ñ` → `n`) y los caracteres no seguros se sustituyen por `_`. Esta decisión está alineada con el comportamiento de WordPress, cuya función de saneamiento de nombres elimina acentos y varios caracteres especiales al gestionar archivos subidos.

De este modo, el nombre que se genera localmente es predecible y no depende de que WordPress lo modifique posteriormente. El contenido de los VTT y manifests continúa escribiéndose en UTF-8, por lo que los textos y transcripciones no pierden Unicode.


## Inferencia inteligente de curso y lección

Cuando el nombre de entrada no sigue estrictamente el formato numérico esperado, el pipeline intenta recuperar información útil sin convertir texto arbitrario en una etiqueta.

- Reconoce marcadores explícitos como `curso`, `course`, `lección`, `lesson`, `capítulo`, `chapter`, `clase`, `tema` y `unidad`.
- Si existe un número fiable, siempre tiene prioridad sobre una inferencia textual.
- Si aparece algo como `Curso posturas estiramientos`, puede inferir `course_name = "posturas estiramientos"`.
- Si aparece `Lección saludo al sol`, puede inferir `lesson_name = "saludo al sol"`.
- Ignora prefijos/sufijos habituales de descarga o compresión como `wetransfer_`, `drive-download-...`, `archive-`, `compressed-`, `copy`, etc.
- No interpreta un nombre arbitrario como curso/lección: por ejemplo, `material-estudio/saludo-inicial.mp4` sigue requiriendo revisión.
- La decisión y el nivel de confianza quedan registrados en `review_required`, `review_reason` y los campos `course_name`/`lesson_name` del manifest.

La inferencia textual es deliberadamente conservadora. Su objetivo es reducir renombrados manuales, no adivinar semántica cuando la estructura de origen no aporta suficiente evidencia.

## Longitud de rutas y nombres

El proyecto **no utiliza un límite fijo universal** para nombres o rutas.

Antes de generar nombres que van a tocar el filesystem local, consulta los límites efectivos del sistema donde se está ejecutando:

- POSIX/Linux/macOS: `os.pathconf()` (`PC_NAME_MAX` y `PC_PATH_MAX`) sobre el filesystem real.
- Windows: límite de componente del volumen mediante `GetVolumeInformationW`; para la ruta completa se usa una política conservadora de `MAX_PATH`, ampliándose únicamente cuando Windows informa de `LongPathsEnabled=1`.

Cuando un componente no cabe, se reduce únicamente lo necesario y se conserva un sufijo corto de unicidad cuando procede. Esto afecta a temporales, resultados locales, manifests, errores y archivos archivados.

Aunque el destino final sea Google Drive, el pipeline sigue necesitando crear archivos temporales localmente antes de subirlos, por lo que estos controles siguen siendo necesarios.

## ZIP procesados

En el proveedor local, cada ZIP se identifica por nombre y SHA-256. Solo se considera procesado cuando existe una entrada `success` con ambos valores.

Cuando se conserva el origen, el ZIP se copia a `storage/archive/sources/`, se verifica su SHA-256, se registra el procesamiento y solo después se elimina de `storage/input/`.

Los estados `partial` y `error` no se consideran procesados.

## Colisiones de resultados

Si un resultado ya existe en el destino, el pipeline no lo sobrescribe silenciosamente. Genera un sufijo corto basado en el origen y, si fuese necesario, un índice adicional. Esto evita que dos ZIP distintos que contengan medios con el mismo nombre terminen pisándose.

## Pruebas

Dependencias de desarrollo:

```bash
.venv/bin/python -m pip install -r requirements-dev.txt
```

Ejecutar tests:

```bash
.venv/bin/python -m pytest -q
```

Los tests cubren extracción ZIP, resolución de FFmpeg, normalización de nombres para WordPress, límites efectivos del filesystem, almacenamiento, configuración, URI, VTT y finalización idempotente de fuentes.

## Empaquetado

Linux/macOS:

```bash
./scripts/build_linux.sh
```

Windows:

```bat
scripts\build_windows.bat
```

Los scripts de build instalan las dependencias de desarrollo antes de ejecutar PyInstaller.

## Seguridad

- No se incluyen credenciales reales en el repositorio.
- Se mantienen los controles contra ZIP traversal.
- Se aplican límites de extracción de ZIP configurables.
- Las rutas y nombres locales se validan/sanean antes de tocar el filesystem.
- Las salidas se escriben en UTF-8.

## Finalización de fuentes locales

Si una fuente desaparece entre el procesamiento y `finalize_source` (por ejemplo, porque Finder, otro proceso o un sincronizador la mueve/elimina), el proceso no convierte un ZIP correctamente procesado en un error. La finalización es idempotente en ese caso y se conserva el resultado generado.

## Reanudación real e idempotencia

Desde la versión 2.3.0 el pipeline guarda un manifest incremental del ZIP en `storage/output/_manifests/`. El manifest se actualiza después de cada vídeo, no solo al final del ZIP. Si una ejecución se interrumpe, en la siguiente ejecución se comprueba cada vídeo individualmente. Un vídeo se considera reutilizable únicamente cuando el manifest registra `status=success` y existen los cuatro artefactos esperados: MP4, MP3, VTT traducido y VTT de transcripción original. En ese caso se marca como `resumed` y no vuelve a ejecutar FFmpeg, Whisper ni la traducción.

Esto permite reanudar una tanda grande sin repetir vídeos que ya terminaron correctamente, incluso cuando la ejecución anterior terminó con un error posterior en el archivado del ZIP de entrada. Los resultados de la ejecución muestran `media_resumed` por ZIP.

Los manifests nuevos incluyen metadatos de versión, identidad de la fuente y configuración relevante. Los manifests antiguos en formato de lista siguen siendo legibles, por lo que las salidas de versiones anteriores pueden reutilizarse siempre que sus artefactos sean verificables.

## Migración de nombres antiguos

La política de salida vuelve a utilizar nombres ASCII normalizados para que los nombres locales sean estables y coincidan con el saneamiento habitual de WordPress. En cada ejecución, antes de intentar reanudar, se inspeccionan las carpetas y archivos existentes bajo el destino y se migran los nombres Unicode o especiales a la versión normalizada cuando no existe una colisión. Los manifests antiguos también se normalizan al validar sus entradas.

La migración nunca elimina un archivo por una simple colisión: si el nombre normalizado ya existe, se conserva el nombre original y se registra una advertencia para revisión.

El comportamiento puede desactivarse con `normalize_legacy_names = false` o, para una ejecución concreta, con `--no-name-migration`.

## Control de reanudación

La reanudación está activada por defecto mediante `resume_enabled = true`. Para forzar una ejecución completa y no reutilizar resultados anteriores se puede usar `--no-resume`. Esto no borra ni sobrescribe automáticamente los resultados existentes; el objetivo de esta opción es evitar que el pipeline los use como checkpoint.

La reanudación se realiza sobre artefactos ya publicados, por lo que también funciona cuando el ZIP fue procesado por una versión anterior pero falló después, por ejemplo durante `finalize_source()`.


## Rendimiento y reanudación

La versión 2.5.0 añade inferencia conservadora de nombres de curso/lección sobre las optimizaciones de 2.4.0:

1. **Reanudación por vídeo**: los vídeos con MP4, MP3, VTT traducido y VTT original válidos se saltan sin volver a transcribir.
2. **Traducción por lotes**: `deep-translator` usa `translate_batch()` por grupos configurables y cae a traducción individual si un lote falla.
3. **Paralelismo limitado**: en almacenamiento local se pueden procesar varios vídeos simultáneamente. El valor recomendado para un MacBook Pro de 16 GB es empezar con `2`.
4. **FFmpeg**: para entradas MP4 se intenta primero `-c copy`/remux para evitar recodificación innecesaria. Si no funciona, se usa la transcodificación H.264/AAC habitual.

Los ajustes principales están en `config/app.toml`:

```toml
[processing]
whisper_model = "small"
whisper_beam_size = 1
whisper_condition_on_previous_text = false
whisper_cpu_threads = 0
translation_batch_size = 40

[workflow]
resume_enabled = true
normalize_legacy_names = true
max_parallel_videos = 2

[ffmpeg]
avoid_reencode = true
```

También se pueden sobreescribir en una ejecución local, por ejemplo:

```bash
./scripts/run_local.sh --parallel-videos 2 --translation-batch-size 40 --whisper-beam-size 1
```

Para una ejecución de prueba conservadora:

```bash
./scripts/run_local.sh --parallel-videos 1
```

### Nombres antiguos y longitud

Los resultados de versiones anteriores se migran a nombres normalizados para WordPress. La migración consulta el límite real del filesystem y aplica el mismo control de longitud que los nombres nuevos. Si el nombre antiguo era demasiado largo, se recorta sin usar un límite fijo global y se conserva un sufijo de desambiguación cuando es necesario. Los manifests locales se actualizan con los nombres migrados para que la reanudación siga funcionando.
