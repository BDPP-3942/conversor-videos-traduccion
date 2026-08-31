# Changelog

## [1.2.2] — Naming Timestamp Cleanup

**Tipo:** PATCH — corrección compatible de la política de nombres.

### Fixed

- Evita que metadatos técnicos de fecha/hora procedentes de ZIP, carpetas extraídas o nombres de origen formen parte de la descripción del curso.
- Amplía la limpieza de formatos de fecha y datetime.
- Elimina timestamps técnicos antes de extraer números o descripciones de curso/lección.
- Evita incorporar timestamps a nombres de carpetas y archivos de salida.

### Validation

- Regresiones de nombres de curso/lección.
- Validación de limpieza de timestamps.
- Suite pytest.
- Ruff lint/formato/seguridad.
- Packaging y auditoría de dependencias.

## [1.2.1] — TTS Installation Fix

**Tipo:** PATCH — corrección compatible de instalación de recursos TTS.

### Fixed

- Corrige la instalación de modelos TTS en Windows ante `PermissionError: [WinError 32]`.
- Cierra los archivos temporales antes de moverlos a su destino.
- Hace consistente el bootstrap de assets TTS entre Windows, Linux y macOS.
- Evita que descargas TTS fallidas dejen archivos temporales bloqueados.

### Compatibility

No cambia el formato de modelos TTS, las variables de configuración, los formatos de salida ni el pipeline TTS.

## [1.2.0] — Naming and TTS Improvements

**Tipo:** MINOR — funcionalidad compatible de naming y bootstrap TTS.

### Added / Improved

- Convención de nombres `[course_number]_[course_description]x[lesson_number]_[lesson_description]` cuando la información está disponible.
- Mejor detección de números/descripciones de curso y lección y soporte para resultados ya procesados.
- Bootstrap TTS capaz de preparar los assets Kokoro bajo `tools/tts/` cuando TTS está habilitado.
- Validación del host de las descargas de modelos TTS.
- Detección de resultados previamente procesados para evitar reprocesado audiovisual innecesario.

## [1.1.0] — Reparación de VTT e integración TTS en el pipeline

**Tipo:** MINOR — funcionalidad compatible para recuperar resultados existentes y ejecutar TTS desde el flujo común.

### Added

- Recuperación automática de VTT originales y traducidos con timestamps inválidos o sintaxis WebVTT no válida.
- Regeneración de STT sobre el vídeo normal existente cuando el VTT original no puede validarse.
- Regeneración de traducción cuando el VTT traducido es inválido o cuando el STT tuvo que reconstruirse.
- Integración de la reparación de VTT antes de TTS.
- Validación final de timestamps después de la segmentación STT por silencios.
- Generación TTS sincronizada desde el VTT traducido validado.
- Reutilización de artefactos TTS existentes cuando siguen siendo válidos.
- Copias de seguridad de VTT antes de sustituir artefactos defectuosos.

### Fixed

- Los cues STT con `start >= end` ya no se propagan como subtítulos utilizables.
- Un VTT histórico inválido ya no bloquea la recuperación.
- Un VTT traducido inválido ya no obliga a repetir STT cuando la transcripción original sigue siendo válida.
- `TTS_ENABLED=true` activa el postprocesado TTS en el pipeline común.
- Los VTT inválidos no se utilizan como entrada de síntesis.

## [1.0.1] — Documentación de instalación y mantenimiento

**Tipo:** PATCH — corrección compatible de documentación y navegación.

### Fixed

- Añadida la guía de instalación referenciada desde `README.md`.
- Corregidos enlaces del índice de documentación.
- Aclarados requisitos, dependencias opcionales, FFmpeg, TTS, modelos, proveedores, cloud, scheduler y packaging.
- Documentado el procedimiento de actualización.

## [1.0.0] — Primera release estable

**Tipo:** primera release estable de esta línea.

**Commit de referencia:** `f0f02540426f24912ff8e6a45f92a008ef83861e`.

### Added

- Pipeline completo de procesamiento audiovisual.
- Normalización mediante FFmpeg.
- Transcripción con Whisper/faster-whisper.
- Segmentación consciente de silencios y timestamps preservados.
- Generación y reprocesado de VTT.
- Traducción con proveedores configurables y fallback.
- Almacenamiento local, Google Drive y rclone.
- Manifests, reanudación e idempotencia.
- Deduplicación conservadora.
- TTS opcional basado en el VTT traducido y corregido.
- Audio TTS por cue sincronizado con los intervalos del VTT.
- MP4 TTS y WebM TTS opcional.
- Validación de artefactos antes de completar etapas.
- CLI, wrappers, ejecución programada y packaging.
- Auditorías de seguridad y dependencias.

## Historial anterior

Antes de establecer la línea de releases de producto `1.x`, el repositorio utilizó versiones internas `4.x` y `5.x`. Esas entradas se conservan en el historial Git y no se reinterpretan retroactivamente como versiones `1.x`.
