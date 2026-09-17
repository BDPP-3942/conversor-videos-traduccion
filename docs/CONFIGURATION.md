# Configuración

La configuración se carga desde `config/app.toml` con sobreescrituras mediante variables de entorno. `.env.default` contiene los valores predeterminados y `.env.example` documenta las variables de entorno compatibles.

## Secciones principales

- `[app]`: proveedor, URI de origen/destino, idiomas de origen/destino y nivel de logging.
- `[local]`: conservación del origen local y política de antigüedad de las entradas.
- `[google_drive]`: identificadores de carpetas de Drive y subdirectorio de transcripción.
- `[rclone]`: rutas del binario/configuración gestionados y remote predeterminado.
- `[providers]`: directorio persistente de perfiles de proveedores.
- `[runtime]`: ajuste de recursos, bloqueo de ejecución y bootstrap/actualización de rclone.
- `[processing]`: Whisper/STT, selección del modelo de traducción local, comportamiento de traducción y límites de seguridad ZIP.
- `[workflow]`: resume, migración de nombres, gestión de duplicados y paralelismo de vídeo.
- `[ffmpeg]`: generación multimedia y configuración de WebM.
- `[tts]`: configuración opcional de Kokoro TTS.

El modelo de traducción local puede configurarse tanto desde `config/app.toml` como mediante las sobreescrituras `LOCAL_TRANSLATION_*` correspondientes. Se admiten dos modelos fijados: MADLAD-400 3B como modelo predeterminado orientado a la calidad y OPUS-MT como modelo ligero de compatibilidad. El repositorio y la revisión deben coincidir con el modelo seleccionado; no se admiten combinaciones arbitrarias de modelo/revisión.

## Sobreescrituras mediante variables de entorno

Las variables habituales incluyen:

```dotenv
STORAGE_PROVIDER=local
SOURCE_URI=local://storage/input
TARGET_URI=local://storage/output
SOURCE_LANG=es
TARGET_LANG=en
WHISPER_MODEL=auto
WHISPER_DEVICE=auto
WHISPER_COMPUTE_TYPE=auto
TRANSLATION_PROVIDER=mistral
TRANSLATION_FALLBACK_PROVIDERS=local,deepl,mymemory
LOCAL_TRANSLATION_MODEL=madlad400-3b-ct2-int8
LOCAL_TRANSLATION_MODEL_DIR=tools/models/translation/madlad400-3b-ct2-int8
LOCAL_TRANSLATION_MODEL_ID=cstr/madlad400-3b-ct2-int8
LOCAL_TRANSLATION_MODEL_REVISION=fd0b55729c074372eb84b52b9309a00dc65c40c4
LOCAL_TRANSLATION_DEVICE=auto
LOCAL_TRANSLATION_COMPUTE_TYPE=auto
LOCAL_TRANSLATION_BEAM_SIZE=2
LOCAL_TRANSLATION_AUTO_DOWNLOAD=false
LOCAL_TRANSLATION_HF_TOKEN=
TTS_ENABLED=false
```

Para seleccionar el modelo ligero OPUS-MT, configura conjuntamente toda la configuración de OPUS:

```dotenv
LOCAL_TRANSLATION_MODEL=opus-mt-es-en-ct2-int8
LOCAL_TRANSLATION_MODEL_DIR=tools/models/translation/opus-mt-es-en-ct2-int8
LOCAL_TRANSLATION_MODEL_ID=Prukario/opus-mt-es-en-ct2-int8
LOCAL_TRANSLATION_MODEL_REVISION=ad91ad1697ea1761111ff4c179400796d085b347
```

`LOCAL_TRANSLATION_HF_TOKEN` es opcional. Las descargas de modelos públicos funcionan sin autenticación; configúralo solo cuando el entorno de Hugging Face requiera autenticación. También se acepta `HF_TOKEN` como alternativa estándar. Un `404 Not Found` para un archivo solicitado se diagnostica como un recurso inexistente en la revisión fijada, no como un fallo de autenticación. El token se utiliza únicamente para la descarga HTTPS y no se almacena junto al modelo.

Consulta `.env.example` para conocer toda la superficie de variables de entorno actualmente compatible. No hagas commit de `.env` ni de credenciales de proveedores.

## Selección del proveedor

El proveedor activo predeterminado se configura en `config/app.toml` y puede sobreescribirse mediante `TRANSLATION_PROVIDER`. Las credenciales de proveedores se configuran mediante los mecanismos existentes de perfiles/entorno. Utiliza la CLI del proveedor en lugar de editar secretos manualmente:

```bash
python main.py provider list
python main.py provider use --help
```

## Configuración y política de nombres

Los nombres no se configuran deliberadamente mediante una plantilla de sustitución libre. La aplicación mantiene una política determinista para que la extracción ZIP, las carpetas de salida generadas y los artefactos generados utilicen las mismas reglas físicas del sistema de archivos.

El contrato de nombres lógicos se representa como:

```text
<curso_o_contenedor>x<nombre_normalizado>
```

`x` separa el ámbito; `_` separa las palabras dentro de cada bloque. El nombre físico canónico está pensado para URL web y metadatos y, por tanto, se normaliza a minúsculas mediante `casefold()`. Unicode se descompone canónicamente con NFD, se eliminan las marcas diacríticas combinantes y se recompone con NFC (`niño` -> `nino`, `Vídeo` -> `video`, `õ` -> `o`). Los emoji/símbolos Unicode se omiten. Las letras de otros scripts se conservan cuando no son diacríticos ni símbolos. Los caracteres no válidos para el sistema de archivos, los caracteres de control, los componentes reservados de Windows y los límites de longitud del sistema de archivos también se gestionan en la frontera física del sistema de archivos.

Esta normalización es deliberadamente determinista e idempotente. No intenta reparar heurísticamente mojibake ni adivinar la grafía que pretendía el usuario.

El ajuste de workflow `normalize_legacy_names` controla la migración de nombres de salida ya existentes. No modifica las reglas de nombres. Cuando está habilitada, la migración se realiza antes del procesamiento normal y no debe sobrescribir silenciosamente un destino existente.

## Concurrencia de vídeo

`max_parallel_videos` controla el límite superior del procesamiento concurrente de vídeo. Su valor efectivo se calcula a partir del dispositivo/modelo de Whisper resuelto, los hilos de CPU, la RAM disponible y, cuando se utiliza CUDA, la memoria de GPU disponible.

- `0` significa **AUTO**: la aplicación selecciona un nivel seguro y conservador de concurrencia a partir del hardware detectado.
- Un valor positivo es un **límite superior**, no una garantía. Si supera el techo seguro del hardware, se limita automáticamente.
- `1` conserva explícitamente la ejecución con un único worker.

El cálculo de recursos deja deliberadamente margen para el sistema operativo, Python y FFmpeg. Por ello, el valor efectivo puede ser inferior al configurado aunque la configuración sea válida.

Este comportamiento se introdujo después de la release `1.2.2` mediante la PR #20 (`perf: enforce safe video concurrency`). Forma parte del comportamiento actual de `main`, pero **no forma parte de la release publicada `1.2.2`**.

## Valores predeterminados importantes

- Resume: activado.
- Deduplicación automática de la salida local: desactivada.
- TTS: desactivado.
- Generación de WebM: desactivada de forma predeterminada; `--generate-webm` la activa explícitamente.
- Actualización automática de rclone: desactivada.
- Dispositivo de Whisper: `auto`.
- Tipo de cálculo de Whisper: `auto`.
- Umbral de silencio de VAD de Whisper: 2000 ms.
- Umbral de silencio para dividir subtítulos de Whisper: 1000 ms.
- Descarga automática de traducción local: desactivada.
- Modelo de traducción local: MADLAD-400 3B CT2 INT8.
- Dispositivo de traducción local: `auto`.
- Tipo de cálculo de traducción local: `auto`.
- Tamaño de beam de traducción local: 2.
