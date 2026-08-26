# Manual operativo — Video Translation Pipeline v5

Este documento describe cómo utilizar el proyecto desde cero y cómo trabajar cuando ya existen resultados procesados. Está escrito para el estado actual de `main` y distingue claramente entre preparación administrativa, ejecución normal, ejecución desatendida y reprocesado.

La aplicación admite tres proveedores de almacenamiento: **local**, **Google Drive** y **rclone**. El núcleo de procesamiento es común: entrada de ZIP, extracción segura, detección/normalización de vídeos, FFmpeg, faster-whisper, traducción, persistencia de resultados y mecanismos de resume/deduplicación.

> Regla operativa: la autenticación y configuración se hacen de forma interactiva solo durante el setup. La ejecución cotidiana debe utilizar `run --scheduled` o equivalente y no debe necesitar navegador ni introducir credenciales.

---

## 1. Formas de ejecutar el proyecto

Hay cuatro formas prácticas de arrancar una ejecución normal:

| Método | Windows | macOS/Linux | Uso recomendado |
|---|---|---|---|
| Python directo | `python main.py ...` | `python3 main.py ...` | Desarrollo, diagnóstico y administración |
| Wrapper local | `scripts\\run_local.bat` | `./scripts/run_local.sh` | Ejecución manual sencilla |
| Wrapper desatendido | `scripts\\run_scheduled.bat` / `run_unattended.bat` | `./scripts/run_scheduled.sh` / `run_unattended.sh` | Scheduler y automatización |
| Ejecutable portable | `VideoTranslationPipeline.exe` | `VideoTranslationPipeline` | Equipo de producción sin depender del entorno Python |

El wrapper local de Windows ejecuta `main.py run` para una orden normal y pasa directamente a `reprocess-subtitles` o `duplicates` cuando esos subcomandos se indican. En macOS/Linux hace la misma función con `.venv/bin/python`. fileciteturn411file0 fileciteturn416file0

El wrapper desatendido da prioridad al ejecutable portable si existe y, en su defecto, usa el entorno virtual y `main.py`. En Windows `run_unattended.bat` ejecuta `run --scheduled` y reserva una ruta específica para `reprocess-subtitles`; en Unix el wrapper construye igualmente `run --scheduled`. fileciteturn417file0 fileciteturn414file0

El ejecutable acepta además `--help`; sin argumentos `main.py` se comporta como `run --scheduled`, por lo que el arranque del ejecutable puede ser desatendido. fileciteturn376file0

---

# PARTE A — PRIMERA INSTALACIÓN Y EJECUCIÓN LIMPIA

## 2. Preparar una instalación limpia

### 2.1. Obtener el proyecto

Clona o copia una versión limpia del repositorio. Trabaja siempre desde la raíz del proyecto:

```text
conversor-videos-traduccion/
├── config/
├── docs/
├── scripts/
├── src/
├── storage/
├── tools/
├── main.py
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
└── ...
```

La aplicación declara Python `>=3.11,<3.14`, por lo que las versiones soportadas para operación son 3.11, 3.12 y 3.13. fileciteturn398file0

### 2.2. Comprobar Python

Windows:

```bat
py -3.13 --version
```

o:

```bat
python --version
```

macOS/Linux:

```bash
python3.13 --version
```

El instalador del proyecto busca 3.13, 3.12 o 3.11 y crea `.venv` con un intérprete compatible. En macOS intenta además recuperar Python 3.13 mediante Homebrew si no encuentra ninguno válido. fileciteturn377file0 fileciteturn378file0

### 2.3. Crear el entorno virtual e instalar dependencias

Windows:

```bat
scripts\setup_env.bat
```

macOS/Linux:

```bash
./scripts/setup_env.sh
```

El instalador crea/reutiliza `.venv`, instala `requirements.txt`, comprueba `imageio-ffmpeg`, ejecuta `doctor` y prepara la estructura de runtime. fileciteturn377file0 fileciteturn378file0

Para Google Drive:

```bat
scripts\setup_env.bat --cloud
```

```bash
./scripts/setup_env.sh --cloud
```

Para incorporar soporte auxiliar de rclone:

```bat
scripts\setup_env.bat --rclone
```

```bash
./scripts/setup_env.sh --rclone
```

Se pueden combinar opciones. Para descargar/preparar el modelo Whisper seleccionado automáticamente durante el setup:

```bat
scripts\setup_env.bat --prefetch-whisper
```

```bash
./scripts/setup_env.sh --prefetch-whisper
```

El modelo no se incluye dentro del ejecutable; se descarga en la caché del usuario cuando se utiliza. fileciteturn378file0 fileciteturn377file0

---

## 3. Inicialización del runtime

Puedes crear explícitamente los directorios runtime mediante:

```bash
python main.py init
```

En Windows puede utilizarse:

```bat
.venv\Scripts\python.exe main.py init
```

La configuración base utiliza, para local:

```text
storage/input/
storage/output/
storage/work/
storage/archive/
storage/failures/
storage/logs/
storage/state/
```

La configuración actual establece por defecto proveedor `local`, entrada `local://storage/input` y salida `local://storage/output`. `resume_enabled`, la normalización de nombres y `rename_processed_duplicates` están activados. fileciteturn410file0

---

## 4. Configuración inicial del proveedor

## 4.1. Local

No necesita OAuth.

La configuración base ya apunta a:

```text
Entrada: storage/input/
Salida:  storage/output/
```

Ejecuta:

```bash
python main.py doctor
```

Antes de procesar un lote conviene comprobar que `config/app.toml`, Python y FFmpeg aparecen correctamente y que el preflight está listo. El comando `doctor` comprueba configuración, versión de Python, perfil de recursos, modelo Whisper, FFmpeg y readiness del proveedor. fileciteturn386file0

---

## 4.2. Google Drive

Primero prepara las dependencias:

```bash
./scripts/setup_env.sh --cloud
```

Después realiza una única autorización interactiva:

```bash
python main.py provider setup-google \
  --profile default \
  --source-folder-id ID_ENTRADA \
  --target-folder-id ID_SALIDA \
  --archive-folder-id ID_ARCHIVO
```

En Windows:

```bat
.venv\Scripts\python.exe main.py provider setup-google --profile default --source-folder-id ID_ENTRADA --target-folder-id ID_SALIDA --archive-folder-id ID_ARCHIVO
```

Se crean/persisten credenciales en:

```text
secrets/providers/google/default/credentials.json
secrets/providers/google/default/token.json
```

y la selección de proveedor/origen/destino queda persistida en el runtime. Google puede renovar silenciosamente el access token cuando existe refresh token; una ejecución `--scheduled` no debe abrir un navegador. fileciteturn374file0

Comprobación sin interacción:

```bash
python main.py provider verify google_drive --profile default
```

---

## 4.3. rclone

Primero prepara el entorno si hace falta soporte adicional:

```bash
./scripts/setup_env.sh --rclone
```

Puedes preparar el binario gestionado mediante:

```bash
./scripts/setup_rclone.sh
```

o en Windows:

```bat
scripts\setup_rclone.bat
```

La configuración utiliza:

```text
tools/rclone/
secrets/rclone/rclone.conf
```

No hace falta una instalación global de rclone para el modo gestionado. fileciteturn396file0 fileciteturn397file0

Después configura el remoto, por ejemplo:

```bash
python main.py provider setup-rclone dropbox_main dropbox --source input --target output
```

Para cambiar el remoto activo:

```bash
python main.py provider use rclone --profile dropbox_main --source rclone://input --target rclone://output
```

Para comprobarlo:

```bash
python main.py provider verify rclone --profile dropbox_main --location input
```

En una ejecución desatendida rclone se utiliza mediante un healthcheck de solo lectura y puede realizar su refresh OAuth normal cuando el backend lo admite. Si requiere autorización de nuevo, el modo `--scheduled` queda en `not_ready` en lugar de abrir un navegador. fileciteturn374file0

---

## 5. Configurar el procesamiento antes del primer lote

La configuración de referencia se encuentra en `config/app.toml`. Entre los parámetros relevantes están:

```toml
[processing]
whisper_model = "auto"
whisper_device = "cpu"
whisper_compute_type = "int8"
whisper_beam_size = 5
whisper_condition_on_previous_text = true
whisper_vad_filter = true
translation_provider = "google"
translation_fallback_providers = ["mymemory"]
translation_retries = 5
translation_batch_size = 0

[workflow]
resume_enabled = true
normalize_legacy_names = true
rename_processed_duplicates = true
max_parallel_videos = 0
```

El perfil automático de recursos decide el modelo y concurrencia según CPU/RAM. `max_parallel_videos = 0` significa selección automática. fileciteturn410file0

Para la salida secundaria:

```toml
[ffmpeg]
generate_webm = true
```

También puede forzarse por ejecución con `--generate-webm` o `--no-webm`. fileciteturn410file0

---

## 6. Preparar el primer lote limpio

Para proveedor local coloca los ZIP directamente en:

```text
storage/input/
```

El pipeline está preparado para:

- ZIP normales;
- ZIP anidados hasta la profundidad configurada;
- exclusión de `.DS_Store`, `__MACOSX` y basura equivalente;
- extracción segura;
- normalización de nombres;
- procesamiento de MP4 y otros formatos de entrada admitidos;
- extracción/conversión de audio con FFmpeg;
- STT con faster-whisper;
- VTT original y traducido;
- resume en ejecuciones posteriores.

Los límites actuales de extracción incluyen hasta 5 niveles de ZIP, 10.000 archivos extraídos y 10 GB de contenido extraído. fileciteturn410file0

En Google Drive coloca los ZIP en la carpeta de entrada configurada. En rclone colócalos en el `source` del remoto activo.

---

## 7. Ejecución limpia: Python directo

### 7.1. Ejecución normal

```bash
python main.py run
```

Para local, si se quiere que el origen/destino sean los definidos en `app.toml`, no hace falta añadir `--provider`, `--source` ni `--target`.

### 7.2. Ejecución desatendida

```bash
python main.py run --scheduled
```

Esta es la forma recomendada cuando el proceso va a ejecutarse de forma automática o sin interacción.

### 7.3. Simular disponibilidad sin procesar

```bash
python main.py run --dry-run
```

Esto valida el readiness y evita iniciar el procesamiento.

---

## 8. Ejecución limpia: wrappers

### Windows

```bat
scripts\run_local.bat
```

Para modo desatendido:

```bat
scripts\run_scheduled.bat
```

### macOS/Linux

```bash
./scripts/run_local.sh
```

Para modo desatendido:

```bash
./scripts/run_scheduled.sh
```

Los wrappers locales están diseñados para reducir la cantidad de opciones que debe escribir el operador y seleccionar automáticamente el intérprete del `.venv`. fileciteturn411file0 fileciteturn416file0

---

## 9. Ejecución limpia: ejecutable portable

Primero compila.

Windows:

```bat
scripts\build_windows.bat
```

La aplicación portable queda en:

```text
dist\VideoTranslationPipeline\
```

Incluye el ejecutable y las carpetas operativas `config`, `secrets`, `storage` y `tools`. El modelo Whisper no se empaqueta dentro del EXE. fileciteturn389file0

Linux/macOS:

```bash
./scripts/build_linux.sh
```

La salida equivalente está en:

```text
dist/VideoTranslationPipeline/
```

El script de Linux utiliza PyInstaller `--onedir`, empaqueta faster-whisper/CTranslate2 y copia las carpetas operativas. fileciteturn390file0

Diagnóstico del ejecutable:

Windows:

```bat
dist\VideoTranslationPipeline\VideoTranslationPipeline.exe doctor
```

Linux/macOS:

```bash
./dist/VideoTranslationPipeline/VideoTranslationPipeline doctor
```

Ejecución normal del ejecutable:

```text
VideoTranslationPipeline.exe run
```

Ejecución desatendida:

```text
VideoTranslationPipeline.exe run --scheduled
```

Por doble clic y sin argumentos, el ejecutable utiliza la entrada equivalente a `run --scheduled` en `main.py`. fileciteturn386file0

---

## 10. Precargar Whisper antes del primer lote

Si no quieres esperar a la primera ejecución para descargar el modelo:

Windows:

```bat
scripts\prefetch_whisper.bat
```

macOS/Linux:

```bash
./scripts/prefetch_whisper.sh
```

Los wrappers seleccionan el entorno Python o el ejecutable disponible y llaman a `prefetch-whisper`. fileciteturn402file0 fileciteturn409file0

---

# PARTE B — AUTOMATIZACIÓN / EJECUCIÓN DESATENDIDA

## 11. Windows Task Scheduler

La instalación de la tarea utiliza el ejecutable compilado y permite pasar argumentos.

Por defecto:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/install_task_scheduler.ps1
```

La acción creada es equivalente a:

```text
VideoTranslationPipeline.exe run --scheduled
```

La tarea se configura para:

- ejecutarse periódicamente cada 5 minutos;
- ignorar una nueva instancia si la anterior sigue ejecutándose;
- arrancar cuando esté disponible;
- limitar una ejecución a 24 horas;
- utilizar una cuenta concreta de Windows con sus credenciales persistentes.

Por tanto, antes de activar la tarea debes hacer la autenticación administrativa de Google/rclone con la misma cuenta que tendrá acceso a `secrets`, `storage` y `tools`. fileciteturn394file0

Para una tarea especial de reprocesado puedes pasar argumentos, por ejemplo:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/install_task_scheduler.ps1 -TaskName "VideoTranslationReprocess" -Arguments "reprocess-subtitles --scheduled --output-folder 37x02_Tema --translate-only"
```

---

## 12. macOS launchd

El proyecto incluye instalación de `LaunchAgent`:

```bash
./scripts/install_launchd.sh
```

Por defecto instala una tarea con:

```text
run --scheduled
```

El intervalo actual es de 300 segundos y los logs van a:

```text
storage/logs/launchd.stdout.log
storage/logs/launchd.stderr.log
```

El script también permite instalar tareas con argumentos especiales, incluyendo reprocesado, por ejemplo:

```bash
./scripts/install_launchd.sh com.video.translation.reprocess reprocess-subtitles --scheduled --output-folder 37x02_Tema --stt-only
```

El ejecutable debe existir en `dist/VideoTranslationPipeline/VideoTranslationPipeline` o en la raíz del proyecto. fileciteturn423file0

---

## 13. Linux cron

Un patrón de operación es:

```cron
*/5 * * * * cd /opt/video-translation-pipeline && ./VideoTranslationPipeline run --scheduled >> storage/logs/scheduler.log 2>&1
```

Para una instalación basada en Python también puede utilizarse:

```cron
*/5 * * * * cd /opt/video-translation-pipeline && .venv/bin/python main.py run --scheduled >> storage/logs/scheduler.log 2>&1
```

Para sistemas permanentes es preferible un usuario de servicio dedicado que sea propietario de `secrets/`, `storage/` y el runtime correspondiente. El proyecto usa además un lock de ejecución para impedir procesos concurrentes. fileciteturn374file0

---

# PARTE C — YA EXISTEN VÍDEOS PROCESADOS

## 14. Regla general al introducir vídeos nuevos en una instalación que ya tiene resultados

**No borres `storage/output`, `storage/state` ni los registros existentes para introducir un nuevo lote.**

Coloca los nuevos ZIP en el origen normal y ejecuta el mismo `run`/`run --scheduled` que utilizas habitualmente.

Con `resume_enabled = true`, el proyecto reutiliza el estado disponible y la lógica de identidad evita volver a procesar innecesariamente recursos ya registrados. La configuración y el comportamiento de nombres también contemplan la presencia de resultados históricos. fileciteturn410file0

En local:

```text
storage/input/
    ├── lote_nuevo_01.zip
    ├── lote_nuevo_02.zip
    └── ...
```

Después:

```bash
python main.py run --scheduled
```

No es necesario mover manualmente los resultados antiguos.

---

## 15. Qué ocurre si el ZIP contiene algo que ya fue procesado

No debes asumir que un nombre de ZIP diferente implica un vídeo nuevo.

El sistema distingue identidad de archivo, nombre normalizado y contenido. La política de duplicados utiliza SHA-256 para identificar contenido idéntico y reserva comparaciones más caras para candidatos de nombre similares. La política de nombres y el registro permiten trabajar con resultados generados con convenciones anteriores. fileciteturn412file0

Cuando un ZIP ya procesado vuelve a entrar y `workflow.rename_processed_duplicates = true`, el flujo puede utilizarlo para actualizar la nomenclatura de una salida histórica en lugar de rehacer innecesariamente todo el procesamiento. El objetivo es que un cambio de política de nombres no obligue a regenerar vídeo, audio, Whisper y traducción. fileciteturn412file0

---

## 16. Corregir solo la traducción de un vídeo existente

Este es el caso más habitual cuando:

- el STT original es correcto;
- los timestamps son correctos;
- la traducción tiene errores;
- quieres cambiar proveedor, fallback o volver a intentar una traducción.

Usa:

```bash
python main.py reprocess-subtitles --output-folder 37x02_Tema --translate-only
```

Windows:

```bat
scripts\reprocess_subtitles.bat --output-folder 37x02_Tema --translate-only
```

macOS/Linux:

```bash
./scripts/reprocess_subtitles.sh --output-folder 37x02_Tema --translate-only
```

Este modo reutiliza la transcripción existente y no ejecuta Whisper ni FFmpeg para volver a crear el medio. La documentación actual especifica que `translate-only` regenera exclusivamente el VTT traducido. fileciteturn412file0

En una instalación con proveedor cloud y ejecución programada:

```bash
python main.py reprocess-subtitles --scheduled --output-folder 37x02_Tema --translate-only
```

El modo programado utiliza el proveedor y target persistidos y no puede cambiar de proveedor mediante argumentos durante la ejecución. fileciteturn386file0

---

## 17. Corregir el STT / timestamps de un vídeo existente

Úsalo cuando el problema sea:

- texto original incorrecto;
- segmentación incorrecta;
- huecos o solapamientos de timestamps;
- palabras reconocidas incorrectamente por Whisper/VAD;
- necesidad de volver a generar la transcripción con otro perfil o configuración.

Comando:

```bash
python main.py reprocess-subtitles --output-folder 37x02_Tema --stt-only
```

El modo `stt-only` regenera la transcripción original y no ejecuta la traducción. fileciteturn412file0

Después de cambiar el STT, la traducción anterior puede haber quedado desalineada conceptualmente, porque una nueva segmentación puede producir diferentes límites `start/end`. Por tanto, cuando el objetivo sea corregir timestamps de forma completa, lo más seguro es hacer un reprocesado completo.

---

## 18. Corregir STT y traducción juntos

Para rehacer ambas fases de subtitulado:

```bash
python main.py reprocess-subtitles --output-folder 37x02_Tema
```

Esto mantiene el vídeo/media existente y vuelve a trabajar las fases de subtítulos. `reprocess-subtitles` está diseñado precisamente para actuar dentro de una salida existente sin regenerar el media principal. fileciteturn412file0

---

## 19. Reprocesar un vídeo por nombre

Cuando la carpeta sea conocida por el nombre del vídeo:

```bash
python main.py reprocess-subtitles --video 37x02_Tema.mp4 --translate-only
```

También puedes hacerlo sin `--output-folder` para el STT:

```bash
python main.py reprocess-subtitles --video 37x02_Tema.mp4 --stt-only
```

La CLI admite selectores alternativos de carpeta, vídeo o `source`. No combines selectores con `--all`. fileciteturn386file0

---

## 20. Reprocesar usando el `source` registrado

Cuando el identificador fiable sea el origen del manifest:

```bash
python main.py reprocess-subtitles --source "curso/carpeta/video.mp4" --translate-only
```

Esto es especialmente útil cuando existen nombres de salida antiguos o ambiguos y el registro del origen es más fiable.

---

## 21. Reprocesar todos los resultados existentes

Para todo el conjunto elegible:

```bash
python main.py reprocess-subtitles --all --stt-only
```

Solo traducción:

```bash
python main.py reprocess-subtitles --all --translate-only
```

STT + traducción:

```bash
python main.py reprocess-subtitles --all
```

No combines `--all` con `--output-folder`, `--video` o `--source`. La aplicación valida esta exclusión. fileciteturn386file0

En el ámbito general cada salida se trata independientemente; un fallo o traducción parcial de una carpeta no implica que todas las demás se detengan. fileciteturn412file0

---

## 22. Qué ocurre con los backups al reprocesar

Antes de sustituir una transcripción o VTT, el reprocesador valida la salida. La versión anterior se conserva mediante backup versionado, evitando sobrescribir backups previos. Además se mantiene historial de reprocesado en el runtime. fileciteturn412file0

Por ello, ante un fallo de una nueva traducción, no es necesario eliminar manualmente el resultado anterior antes de reintentar.

---

# PARTE D — NOMBRES Y RESULTADOS HISTÓRICOS

## 23. Normalización de nombres de resultados ya existentes

Hay que diferenciar dos problemas:

### A. Quiero seguir procesando vídeos nuevos

No ejecutes herramientas de deduplicación o renombrado a mano. Añade el nuevo ZIP al input y usa `run --scheduled`.

### B. Quiero actualizar la nomenclatura de un resultado antiguo

La reconstrucción dispone de `rename_processed_duplicates = true` para permitir la migración de resultados históricos hacia la política actual de nombres. Si se vuelve a introducir una fuente ya procesada, la aplicación puede extraerla temporalmente, volver a inferir curso/lección/descripción y renombrar carpeta y artefactos existentes sin rehacer las fases costosas. fileciteturn412file0

No debes confundir esto con `reprocess-subtitles`: el primero es migración/nomenclatura; el segundo corrige subtítulos.

---

## 24. Duplicados de salida

La ejecución normal local incluye limpieza automática de duplicados después del procesamiento. La política es conservadora: una carpeta no se elimina solo porque tenga un nombre parecido; la identidad se basa en contenido generado y el borrado se realiza solo cuando existe un referente claramente mejor según la política de nombres. fileciteturn412file0

Para inspección manual, la CLI actual es:

```bash
python main.py duplicates scan --target "/ruta/storage/output"
python main.py duplicates analyze --target "/ruta/storage/output"
python main.py duplicates delete --target "/ruta/storage/output"
```

Para simular el borrado:

```bash
python main.py duplicates delete --target "/ruta/storage/output" --dry-run
```

**No utilizar `dedupe-output`: esa referencia del README anterior está obsoleta. La CLI actual utiliza el subcomando `duplicates`.**

---

# PARTE E — MATRIZ DE DECISIÓN

## 25. Qué comando utilizar según el problema

| Situación | Acción |
|---|---|
| Instalación nueva, sin resultados | `run` |
| Instalación nueva y ejecución automática | `run --scheduled` |
| Quiero comprobar entorno/proveedor/FFmpeg | `doctor` |
| Quiero precargar Whisper | `prefetch-whisper` |
| Hay vídeos nuevos y resultados antiguos | ejecutar `run` normalmente; no borrar resultados antiguos |
| STT correcto, traducción incorrecta | `reprocess-subtitles --translate-only` |
| STT/timestamps incorrectos | `reprocess-subtitles --stt-only` |
| Quiero rehacer STT y traducción | `reprocess-subtitles` |
| Quiero reprocesar un resultado concreto | `--output-folder`, `--video` o `--source` |
| Quiero reprocesar todo | `--all` |
| Quiero analizar duplicados | `duplicates scan` / `duplicates analyze` |
| Quiero ver qué se borraría | `duplicates delete --dry-run` |
| Quiero limpiar duplicados de forma normal | el pipeline local ya aplica la limpieza automática |
| Quiero actualizar nombres históricos | flujo de migración/renombrado de resultados procesados |

---

# PARTE F — PROCEDIMIENTOS RECOMENDADOS

## 26. Procedimiento completo para una máquina nueva

### Local

```bash
./scripts/setup_env.sh
python main.py doctor
./scripts/prefetch_whisper.sh
./scripts/run_local.sh
```

En Windows:

```bat
scripts\setup_env.bat
.venv\Scripts\python.exe main.py doctor
scripts\prefetch_whisper.bat
scripts\run_local.bat
```

### Google Drive

```bash
./scripts/setup_env.sh --cloud
python main.py provider setup-google --profile default --source-folder-id ID_ENTRADA --target-folder-id ID_SALIDA --archive-folder-id ID_ARCHIVO
python main.py provider verify google_drive --profile default
python main.py doctor
python main.py run --scheduled
```

### rclone

```bash
./scripts/setup_env.sh --rclone
./scripts/setup_rclone.sh
python main.py provider setup-rclone NOMBRE_REMOTO BACKEND --source input --target output
python main.py provider verify rclone --profile NOMBRE_REMOTO --location input
python main.py doctor
python main.py run --scheduled
```

---

## 27. Procedimiento para añadir un lote nuevo a una máquina que ya está en producción

1. No limpies `storage/output`.
2. No elimines `storage/state`.
3. No borres los manifests ni el historial.
4. Introduce el nuevo ZIP en el origen correspondiente.
5. Ejecuta el modo normal/desatendido:

```bash
python main.py run --scheduled
```

6. Revisa `storage/logs/` y el resultado JSON de la ejecución.
7. Solo usa `reprocess-subtitles` si el problema afecta a un resultado ya existente.

La ventaja de este procedimiento es que los resultados anteriores quedan disponibles para resume, identidad y deduplicación. `resume_enabled` está activado en la configuración base. fileciteturn410file0

---

## 28. Procedimiento para corregir un resultado defectuoso

### Error de traducción

```bash
python main.py reprocess-subtitles --output-folder NOMBRE --translate-only
```

### Error de transcripción

```bash
python main.py reprocess-subtitles --output-folder NOMBRE --stt-only
```

### Error completo de subtítulos

```bash
python main.py reprocess-subtitles --output-folder NOMBRE
```

Después revisa el VTT resultante y el historial de reprocesado.

---

## 29. Procedimiento para varios vídeos defectuosos

No hace falta rehacer todos los medios.

Puedes reprocesar todos los subtítulos existentes:

```bash
python main.py reprocess-subtitles --all --translate-only
```

o:

```bash
python main.py reprocess-subtitles --all --stt-only
```

Si el problema es conocido solo en determinadas carpetas, es preferible reprocesado selectivo para reducir tiempo de CPU y llamadas de traducción.

---

# PARTE G — DIAGNÓSTICO Y SEGURIDAD

## 30. Si la ejecución devuelve `not_ready`

Ejecuta:

```bash
python main.py doctor
```

Después comprueba según proveedor:

```bash
python main.py provider verify google_drive --profile default
```

```bash
python main.py provider verify rclone --profile NOMBRE_REMOTO --location input
```

En un scheduler no intentes iniciar OAuth manualmente desde el proceso automático. Repara la autorización administrativamente y vuelve a ejecutar el lote. El diseño del proyecto evita abrir navegador en `--scheduled`. fileciteturn374file0

---

## 31. Si falla una traducción

La configuración actual contempla proveedor principal, fallback, reintentos, espera mínima entre peticiones y backoff. Esto está definido en `[processing]` dentro de `config/app.toml`. fileciteturn410file0

Cuando el lote queda parcial, el procedimiento correcto es:

1. conservar los resultados generados;
2. consultar logs;
3. corregir credenciales/proveedor si corresponde;
4. utilizar `reprocess-subtitles --translate-only` para regenerar solo los VTT afectados.

No borres el vídeo ni vuelvas a transcribir sin necesidad.

---

## 32. Si hay desajuste de timestamps

El diagnóstico del reprocesado compara huecos y solapamientos. La traducción conserva los mismos `start/end` que recibe del STT. Por tanto:

```text
timestamps ya incorrectos en STT
        ↓
problema de Whisper/VAD/segmentación

STT correcto + texto traducido incorrecto
        ↓
problema de traducción/proveedor
```

En el primer caso usa `--stt-only` o reprocesado completo; en el segundo usa `--translate-only`. fileciteturn412file0

---

## 33. Secretos y cuentas

No versionar:

```text
secrets/
config/runtime.toml
```

Los ficheros `token.json`, `credentials.json` y `rclone.conf` deben tratarse como secretos. El ejecutable no contiene credenciales. La cuenta del scheduler debe tener únicamente los permisos necesarios. fileciteturn419file0

---

# PARTE H — RESUMEN DE REFERENCIA RÁPIDA

## Ejecución nueva

```bash
python main.py run
```

## Ejecución desatendida

```bash
python main.py run --scheduled
```

## Diagnóstico

```bash
python main.py doctor
```

## Precargar Whisper

```bash
python main.py prefetch-whisper
```

## STT de un resultado existente

```bash
python main.py reprocess-subtitles --output-folder NOMBRE --stt-only
```

## Traducción de un resultado existente

```bash
python main.py reprocess-subtitles --output-folder NOMBRE --translate-only
```

## STT + traducción de un resultado existente

```bash
python main.py reprocess-subtitles --output-folder NOMBRE
```

## Todos los resultados

```bash
python main.py reprocess-subtitles --all
```

## Duplicados

```bash
python main.py duplicates scan --target storage/output
python main.py duplicates analyze --target storage/output
python main.py duplicates delete --target storage/output --dry-run
```

## Ejecutable Windows

```text
VideoTranslationPipeline.exe run --scheduled
```

## Ejecutable Unix

```bash
./VideoTranslationPipeline run --scheduled
```

---

## 34. Principio operativo final

En una instalación limpia, primero se prepara el entorno, se configura el proveedor y se valida `doctor`; después se hace la ejecución normal o desatendida.

En una instalación con historial, **no se reinicia el proyecto desde cero para cada lote**. Los resultados existentes forman parte del estado operativo. Los vídeos nuevos se procesan mediante `run`; los resultados defectuosos se corrigen mediante `reprocess-subtitles`; y la deduplicación/migración de nombres se mantiene separada del reprocesado de subtítulos.

La elección correcta es siempre el proceso mínimo que resuelve el problema:

```text
VÍDEO NUEVO
    ↓
run

TRADUCCIÓN INCORRECTA
    ↓
reprocess-subtitles --translate-only

STT / TIMESTAMPS INCORRECTOS
    ↓
reprocess-subtitles --stt-only

STT + TRADUCCIÓN INCORRECTOS
    ↓
reprocess-subtitles

RESULTADOS HISTÓRICOS CON NOMBRES ANTIGUOS
    ↓
migración / renombrado

DUPLICADOS DE SALIDA
    ↓
política automática + duplicates para inspección explícita
```
