# Changelog

## [1.1.0] — Reparación de VTT e integración TTS en el pipeline

**Tipo:** MINOR — funcionalidad compatible para recuperar resultados existentes y ejecutar TTS desde el flujo común.

### Added

- Recuperación automática de VTT originales y traducidos con timestamps inválidos o sintaxis WebVTT no válida.
- Regeneración de STT sobre el vídeo normal existente cuando el VTT original no puede validarse.
- Regeneración de traducción cuando el VTT traducido es inválido o cuando el STT tuvo que reconstruirse.
- Integración de la reparación de VTT antes de TTS para ejecuciones nuevas y resultados ya procesados.
- Validación final de timestamps después de la segmentación STT por silencios.
- Generación TTS sincronizada desde el VTT traducido validado mediante el mismo backend de almacenamiento.
- Reutilización de artefactos TTS existentes cuando siguen siendo válidos.
- Copias de seguridad de VTT antes de sustituir artefactos defectuosos.
- Tests de regresión para los tres escenarios principales de recuperación.

### Fixed

- Los cues STT con `start >= end` ya no se propagan como subtítulos utilizables.
- Un VTT histórico inválido ya no bloquea el intento de recuperación antes de poder regenerar STT.
- Un VTT traducido inválido ya no obliga a repetir STT cuando la transcripción original sigue siendo válida.
- `TTS_ENABLED=true` activa realmente el postprocesado TTS en el pipeline común.
- Los VTT inválidos no se utilizan como entrada de síntesis.

### Documentation

- Añadida `docs/VTT_REPAIR.md` con los tres escenarios de recuperación y las garantías de seguridad.
- Actualizadas las instrucciones de TTS, instalación y ejecución sobre resultados existentes.

## [1.0.1] — Documentación de instalación y mantenimiento

**Tipo:** PATCH — corrección compatible de documentación y navegación del proyecto.

### Fixed

- Añadida la guía de instalación que era referenciada desde `README.md`.
- Corregidos los enlaces del índice de documentación del README para no apuntar a documentos inexistentes.
- Aclarados los requisitos de Python, dependencias opcionales, FFmpeg, TTS, modelos externos, proveedores de traducción, almacenamiento cloud, ejecución programada y empaquetado.
- Documentado el procedimiento de actualización y validación de una instalación existente.

## [1.0.0] — Primera release estable

**Tipo:** MAJOR — primera release estable de esta línea de producto.

**Commit de referencia:** `f0f02540426f24912ff8e6a45f92a008ef83861e`

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

### Fixed

- Conservación de pausas largas en la segmentación de subtítulos.
- Duración del vídeo cuando la narración TTS termina antes.
- Nombres lógicos de carpetas en manifests cloud.
- Configuración de perfiles de recursos y deduplicación.
- Compatibilidad con Ruff lint y formato canónico.

## Historial anterior

Antes de establecer la línea de releases de producto `1.x`, el repositorio utilizó versiones internas `4.x` y `5.x` durante la reconstrucción y evolución del pipeline. Esas entradas se conservan en el historial Git y en las releases/tag que ya existan, pero no se reinterpretan retroactivamente como versiones `1.x`.

## Próximas versiones

- `1.1.x` — correcciones compatibles sobre la recuperación y TTS.
- `1.2.0` — siguiente conjunto de funcionalidad nueva compatible.
- `2.0.0` — solo ante cambios incompatibles de contrato o arquitectura pública.
