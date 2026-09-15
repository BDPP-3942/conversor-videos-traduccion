# Resumen del proyecto

## Propósito

**Video Translation Pipeline** es una aplicación Python orientada al procesamiento por lotes para la localización audiovisual. Acepta vídeos o paquetes ZIP, normaliza los medios, transcribe el habla, crea y valida subtítulos WebVTT, traduce sus segmentos conservando los tiempos y puede sintetizar narración sincronizada mediante Kokoro TTS.

Está diseñada para ejecución desatendida y admite almacenamiento local, Google Drive y rclone.

## Alcance

Las capacidades implementadas incluyen:

- ingestión de vídeos y ZIP;
- procesamiento multimedia mediante FFmpeg;
- STT con `faster-whisper`;
- segmentación basada en silencios y validación VTT;
- proveedores de traducción configurables con respaldo y reintentos;
- adaptadores local, Google Drive y rclone;
- manifests, reanudación/idempotencia y validación de artefactos;
- gestión conservadora de duplicados;
- TTS Kokoro sincronizado opcional;
- concurrencia adaptada a CPU, RAM y GPU disponible;
- CLI y ejecución desatendida;
- programación mediante los mecanismos de Windows, macOS y Linux;
- aplicación de escritorio multiplataforma y empaquetado nativo;
- pruebas, linting, seguridad, empaquetado y auditoría de dependencias.

La aplicación no es un editor audiovisual interactivo y los resultados automáticos de traducción/TTS requieren revisión humana cuando la exactitud sea crítica.

## Contrato de ejecución

El punto de entrada canónico es `main.py`. El paquete también expone `video-translation-pipeline`, `video-translation-regenerate`, `video-subtitle-qa`, `video-translation-tts` y `video-translation-desktop`.

En modo local, la aplicación de escritorio utiliza por defecto:

```text
Documentos/Video Translation Pipeline/input
                    ↓
                 pipeline
                    ↓
Documentos/Video Translation Pipeline/output
```

El estado interno, logs y cachés se mantienen separados en el directorio privado de datos de la aplicación. Las carpetas `input` y `output` pueden sustituirse por cualquier ubicación con permisos de escritura.

Consulta [`INSTALLATION.md`](INSTALLATION.md), [`CONFIGURATION.md`](CONFIGURATION.md), [`CLI.md`](CLI.md) y [`DESKTOP.md`](DESKTOP.md).

## Release candidata actual

La candidata actual es `1.10.0`. Es una release `MINOR` que añade la aplicación de escritorio, el empaquetado nativo, la reparación de nombres Unicode en ZIP y la arquitectura de almacenamiento de trabajo separada del estado privado.

La publicación de `v1.10.0` requiere que CI y Release Gate estén verdes sobre el SHA final y que se actualicen de forma coherente [`pyproject.toml`](../pyproject.toml), [`config/app.toml`](../config/app.toml), [`uv.lock`](../uv.lock), [`CHANGELOG.md`](../CHANGELOG.md) y [`docs/RELEASES.md`](RELEASES.md).

Las releases publicadas anteriores son inmutables. Consulta [`RELEASES.md`](RELEASES.md) para el historial.

## Cambios principales de 1.10.0

### Aplicación de escritorio

- Interfaz Tk/ttk sobre la fachada de aplicación existente.
- Ejecución explícita mediante botón principal.
- Configuración de almacenamiento, idiomas, traducción, Whisper, FFmpeg, TTS, concurrencia, resume y naming.
- Selección de archivo de contexto para Whisper.
- Recuperación de subtítulos, deduplicación y diagnóstico.
- Progreso, logs, ejecución en segundo plano y cancelación cooperativa.

### Almacenamiento

- `input` y `output` predeterminados en `Documentos/Video Translation Pipeline`.
- Estado interno separado en datos privados del usuario.
- Selección libre de carpetas compartidas, de red o sincronizadas siempre que el usuario tenga permisos de escritura.
- Ninguna operación normal de procesamiento necesita escribir en `Program Files`.

### ZIP y Unicode

La extracción corrige los nombres UTF-8 que han sido interpretados erróneamente como CP437 cuando el ZIP no contiene el indicador UTF-8. La detección es conservadora para no reinterpretar nombres CP437 legítimos.

La reparación de extracción y la normalización física posterior son capas distintas: un nombre legítimo como `niño` puede conservarse al extraer y convertirse después en `nino` por la política de nombres de salida.

### Windows

El instalador MSI se construye con la arquitectura real del ejecutable. El build x64 utiliza `Program Files`; un build x86 utiliza la ubicación de programas de 32 bits correspondiente. No se declara que un ejecutable x64 pueda ejecutarse en Windows x86.

El MSI crea un acceso directo en el menú Inicio y la aplicación no requiere escritura en su directorio de instalación.

### CLI y documentación

- Las descripciones `description=` y `help=` de los parsers CLI deben estar en español.
- [`CLI.md`](CLI.md) es la referencia de uso y documenta los casos de uso públicos, incluyendo comandos, opciones, wrappers y ejemplos.
- Los ejemplos de comandos explican qué comprueban o modifican y sus restricciones relevantes.
- Las referencias a otros documentos utilizan enlaces Markdown relativos.
- Los comentarios y docstrings modificados para esta release conservan el contenido técnico en español.
- Las reglas se aplican directamente sobre los ficheros canónicos; no existe un `INDEX.md` auxiliar que deba mantenerse sincronizado.

## Evidencia de releases

| Capacidad | Primera release verificada |
| --- | ---: |
| Pipeline audiovisual, STT, VTT, traducción, almacenamiento, resume, deduplicación, TTS y programación | `1.0.0` |
| Recuperación VTT e integración TTS | `1.1.0` |
| Naming y bootstrap de TTS | `1.2.0` |
| Concurrencia adaptada a recursos | `1.3.0` |
| Regeneración limpia | `1.4.0` |
| Whisper/contexto/empaquetado multiplataforma | `1.5.0` |
| Endurecimiento ZIP/filesystem | `1.5.1` |
| Traducción local y endurecimiento GPU/runtime | `1.6.0` |
| Reprocessing, manifests y naming Unicode | `1.7.0` |
| Recuperación Whisper refinada y modelos locales fijados | `1.8.0` |
| Bootstrap gestionado de uv | `1.8.1` |
| Corrección MADLAD/tokenizer/diagnóstico Hugging Face | `1.8.2` |
| Resolución gestionada de uv en wrappers | `1.8.3` candidata histórica |
| Aplicación GUI, empaquetado nativo, reparación ZIP Unicode y almacenamiento de escritorio | `1.10.0` candidata |

## Documentación canónica

- [`ARCHITECTURE.md`](ARCHITECTURE.md)
- [`USE_CASES.md`](USE_CASES.md)
- [`PIPELINE.md`](PIPELINE.md)
- [`INSTALLATION.md`](INSTALLATION.md)
- [`CONFIGURATION.md`](CONFIGURATION.md)
- [`CLI.md`](CLI.md)
- [`DESKTOP.md`](DESKTOP.md)
- [`PACKAGING.md`](PACKAGING.md)
- [`STORAGE.md`](STORAGE.md)
- [`SUBTITLES.md`](SUBTITLES.md)
- [`TRANSLATION.md`](TRANSLATION.md)
- [`TRANSLATION_PROVIDERS.md`](TRANSLATION_PROVIDERS.md)
- [`TTS.md`](TTS.md)
- [`RESUME.md`](RESUME.md)
- [`DEDUPLICATION.md`](DEDUPLICATION.md)
- [`SCHEDULING.md`](SCHEDULING.md)
- [`SECURITY.md`](SECURITY.md)
- [`TESTING.md`](TESTING.md)
- [`CI_CD.md`](CI_CD.md)
- [`DEVELOPMENT.md`](DEVELOPMENT.md)
- [`TROUBLESHOOTING.md`](TROUBLESHOOTING.md)
- [`RELEASES.md`](RELEASES.md)
- [`REGENERATION.md`](REGENERATION.md)
- [`LOCAL_TRANSLATION.md`](LOCAL_TRANSLATION.md)
- [`CUDA.md`](CUDA.md)
- [`UNINSTALLATION.md`](UNINSTALLATION.md)
