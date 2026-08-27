# Video Translation Pipeline

Pipeline multiplataforma para automatizar la localización de vídeos: ingesta, normalización audiovisual, transcripción, traducción, subtítulos, narración TTS sincronizada y entrega local o cloud.

## Qué resuelve

```text
Vídeo / ZIP
   ↓
FFmpeg + validación
   ↓
Whisper / VAD
   ↓
VTT original
   ↓
Traducción
   ↓
VTT final
   ├────────→ subtítulos
   ├────────→ vídeo normal
   └────────→ TTS opcional
                 ↓
             audio por cue
                 ↓
             MP4 / WebM
```

Los timestamps del VTT final son la fuente de verdad. Los silencios relevantes se conservan desde STT hasta traducción y TTS.

## Alcance

- Procesamiento por lotes de vídeos y ZIP.
- Entrada/salida local, Google Drive y backends de rclone.
- Normalización y generación audiovisual con FFmpeg.
- STT con Whisper/faster-whisper y segmentación basada en silencios.
- Traducción con proveedores configurables y fallback.
- VTT, validación y reprocesado selectivo/general.
- TTS opcional sincronizado con el VTT traducido/corregido.
- MP4 TTS y WebM TTS opcional.
- Manifests, resume e idempotencia.
- Deduplicación conservadora.
- CLI, wrappers, ejecutable y ejecución programada.
- CI, auditoría de seguridad y auditoría de dependencias.

No es un editor audiovisual interactivo ni sustituye la revisión humana de traducciones o locuciones.

## Objetivos

1. Automatizar procesamiento repetitivo y por lotes.
2. Mantener sincronización temporal fiable, incluidos silencios largos.
3. Separar lógica de negocio de proveedores externos.
4. Reanudar sin repetir etapas válidas.
5. Validar resultados antes de marcarlos como completos.
6. Permitir operación desatendida y multiplataforma.
7. Mantener una base de código mantenible y auditable.

## Inicio rápido

### Entorno local

Instala las dependencias según [`docs/INSTALLATION.md`](docs/INSTALLATION.md), configura `config/app.toml` y coloca las entradas en `storage/input/`.

```bash
python main.py doctor
python main.py --help
python main.py run
```

Para operación desatendida:

```bash
python main.py run --scheduled
```

### Reprocesado

```bash
python main.py reprocess-subtitles --all --stt-only
python main.py reprocess-subtitles --all --translate-only
python main.py reprocess-subtitles --all
```

## TTS

TTS está desactivado por defecto para conservar el comportamiento histórico. Cuando se habilita, usa el VTT traducido y corregido como entrada, genera audio por cue y lo coloca dentro de sus intervalos temporales. Los huecos entre cues permanecen como silencio.

Consulta [`docs/TTS.md`](docs/TTS.md) para configuración, proveedores, sincronización, modelos y licencias.

## Almacenamiento

El núcleo de procesamiento es común a todos los modos:

```text
CLI / wrapper / ejecutable / scheduler
                  ↓
             pipeline común
                  ↓
        adapter de almacenamiento
          ↙                    ↘
       local             Google Drive/rclone
```

La autenticación cloud se configura administrativamente y no debe requerir interacción durante una ejecución programada.

## Reanudación

El manifest diferencia etapas y artefactos. Un archivo existente se reutiliza solo después de validarlo. Un fallo recuperable afecta a la etapa correspondiente y permite reintentarla.

TTS puede ser opcional o obligatorio. En modo opcional, un fallo de TTS no invalida los resultados tradicionales; en modo obligatorio, el trabajo permanece incompleto hasta generar los artefactos requeridos.

## Ejecución programada y ejecutable

El proyecto contempla Windows Task Scheduler, macOS launchd, cron cuando esté configurado y builds PyInstaller. Las tareas deben usar un directorio de trabajo determinista y no depender de una terminal o virtualenv interactivo.

## Calidad

La CI comprueba tests, lint, formato, seguridad, compilación, packaging y dependencias. Localmente:

```bash
pytest
ruff check .
ruff format --check .
python -m compileall .
```

## Documentación

| Documento | Propósito |
|---|---|
| [`docs/INSTALLATION.md`](docs/INSTALLATION.md) | Instalación, dependencias, entorno y puesta en marcha |
| [`docs/PROJECT_GUIDE.md`](docs/PROJECT_GUIDE.md) | Alcance funcional y funcionamiento completo |
| [`docs/TTS.md`](docs/TTS.md) | TTS, sincronización, artefactos y licencias |
| [`docs/TRANSLATION_PROVIDERS.md`](docs/TRANSLATION_PROVIDERS.md) | Proveedores de traducción y fallback |
| [`docs/UNATTENDED.md`](docs/UNATTENDED.md) | Scheduler y ejecución sin interacción |
| [`docs/DEDUPLICATION.md`](docs/DEDUPLICATION.md) | Deduplicación y limpieza segura |
| [`docs/SECURITY.md`](docs/SECURITY.md) | Seguridad y gestión de secretos |
| [`docs/AUDIT.md`](docs/AUDIT.md) | Auditoría técnica y riesgos conocidos |
| [`docs/RELEASES.md`](docs/RELEASES.md) | Política e histórico de releases |
| [`CHANGELOG.md`](CHANGELOG.md) | Cambios orientados al usuario |

Los detalles de configuración y CLI se documentan actualmente junto al funcionamiento y los comandos en `README.md`, `PROJECT_GUIDE.md`, `INSTALLATION.md` y las guías especializadas. No se mantienen enlaces a documentos inexistentes.

## Versionado

Se usa Semantic Versioning:

- `MAJOR`: incompatibilidades.
- `MINOR`: funcionalidad nueva compatible.
- `PATCH`: correcciones, seguridad, documentación y mantenimiento.

La línea de releases de producto comienza en **1.0.0**. El historial previo del paquete Python en `5.x` queda explicado en [`docs/RELEASES.md`](docs/RELEASES.md) para evitar confundir versión interna con release de producto.

## Seguridad y licencias

No versionar secretos, tokens ni claves. Los modelos, pesos y voces TTS pueden tener licencias diferentes de las librerías que los ejecutan. Antes de redistribuir el ejecutable o usarlo comercialmente debe revisarse la licencia concreta de cada componente.
