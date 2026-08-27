# Auditoría integral del proyecto

Fecha de revisión: 2026-08-27

## Alcance

Se revisaron el pipeline principal, STT/VTT, traducción, QA de subtítulos, FFmpeg, deduplicación, manifests/resume, almacenamiento local, Google Drive, rclone, autenticación, configuración, CLI, scripts `run_local`/unattended, packaging, tareas programadas, tests y GitHub Actions.

## Arquitectura verificada

Los entrypoints deben converger en `main.py` y `MediaPipeline`. Local, Google Drive y rclone implementan `StorageProvider`; TTS se integra como decorator (`TTSAwareStorageProvider`) y no como un segundo pipeline.

## Hallazgos corregidos en esta PR

### STT y silencios

Whisper se ejecutaba anteriormente con segmentos completos como timestamps de VTT. Un segmento podía atravesar una pausa interna larga y mantener el subtítulo visible durante el silencio. Ahora se solicitan `word_timestamps` y se divide un segmento cuando existe una pausa interna igual o superior a `whisper_min_silence_duration_ms` (1.5 s por defecto). El VTT traducido conserva esos timestamps.

### TTS

El TTS utiliza el VTT traducido/corregido como fuente de verdad, genera audio por cue, conserva silencios, reintenta con mayor velocidad cuando el audio no cabe y rechaza solapamientos. Genera MP4 TTS y WebM TTS cuando corresponda.

### Seguridad Ruff S603

Las llamadas FFmpeg del módulo TTS se construyen como argv, sin shell, con el ejecutable resuelto a una ruta absoluta existente y con entradas de vídeo/audio también resueltas. Ruff S603 es una regla heurística que no puede demostrar esas garantías; se conserva un `noqa: S603` local y documentado únicamente en esas dos llamadas.

No se usa `shell=True`.

### Deduplicación

Se detectó una inconsistencia de configuración: `main.py` podía activar la deduplicación automática local mediante `getattr(..., True)` aunque no existiera un campo equivalente en `AppSettings`. Ahora `automatic_output_deduplication` existe explícitamente y su valor predeterminado es `false`, preservando el comportamiento anterior y evitando eliminaciones automáticas inesperadas.

### TTS CLI

`--output-folder` se limita a un único nombre de carpeta relativo bajo `storage/output`. Se rechazan rutas absolutas y componentes `..`.

### CI/CD

CI comprueba ahora los tres entrypoints instalados, incluyendo `video-translation-tts`, y existe un job independiente que instala el extra `[tts]` y ejecuta `pip-audit --strict` sobre esa dependencia opcional.

## Seguridad revisada

- ZIP path traversal: protegido mediante `Path.resolve()` + `is_relative_to()`.
- ZIP symlinks: rechazados.
- límites de archivos/tamaño/profundidad: aplicados.
- subprocess: argv sin shell y timeouts en FFmpeg/rclone.
- rclone descargado: SHA-256 verificado antes de instalarlo.
- Google token: almacenado fuera del árbol de configuración pública y con permisos 0600 cuando el sistema los soporta.
- APIs HTTP: proveedores de traducción fuerzan HTTPS; QA local acepta HTTP únicamente para servicios explícitamente configurables/locales.
- secretos: no se almacenan en el repositorio.
- CLI TTS: restringido al árbol de resultados local.

## Riesgos/limitaciones que requieren validación operativa

1. Google Drive y rclone requieren credenciales reales para probar una subida completa.
2. La generación TTS real requiere pesos Kokoro y no debe ejecutarse en CI estándar.
3. El ejecutable comercial debe revisarse junto con todas las licencias transitivas efectivamente empaquetadas por PyInstaller.
4. No se debe afirmar que el flujo cloud ha sido validado sin ejecutar una transferencia real con una cuenta de prueba.

## Política de estados

Un fallo TTS no invalida los resultados tradicionales cuando `tts_required=false`. Cuando `tts_required=true`, la fuente no se finaliza hasta que TTS haya terminado correctamente. Los manifiestos registran el estado TTS y los artefactos generados.

## Conclusión

La revisión no se limita a lint. Se han auditado las fronteras entre entrada, extracción, STT, traducción, QA, generación multimedia, almacenamiento, estado, autenticación y ejecución desatendida. Los cambios se mantienen centrados en problemas funcionales o de seguridad verificables y no realizan una reescritura cosmética del proyecto.