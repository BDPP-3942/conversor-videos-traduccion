# Changelog

## [1.1.0] — Recuperación de VTT e integración TTS en el pipeline

**Tipo:** MINOR — nueva funcionalidad compatible para recuperación de resultados existentes y generación TTS desde `run`.

### Added

- Recuperación automática de VTT originales y traducidos con timestamps inválidos.
- Regeneración de STT sobre el vídeo normal existente cuando el VTT original no puede validarse.
- Regeneración de traducción cuando el VTT traducido es inválido o el STT tuvo que reconstruirse.
- Validación final de timestamps después de la segmentación por silencios.
- Integración de TTS en `python main.py run` mediante `TTS_ENABLED=true`.
- Generación de WAV, MP4 TTS y WebM TTS opcional usando el mismo backend de almacenamiento.
- Reutilización de TTS ya existente cuando los subtítulos no han cambiado.
- Regeneración de TTS cuando la reparación de VTT cambia su fuente temporal o textual.
- Documentación específica de recuperación de VTT.

### Fixed

- Los cues STT con `start >= end` ya no se propagan como subtítulos utilizables.
- El reprocesador ya no bloquea la recuperación por encontrar primero un VTT histórico inválido.
- `TTS_ENABLED=true` deja de ser una configuración sin efecto en `main.py run`.
- Los VTT inválidos no se utilizan como entrada para TTS.

### Documentation

- Actualizado `README.md` para reflejar la integración real de TTS.
- Actualizado `docs/TTS.md` con el flujo real y recuperación de VTT.
- Añadido `docs/VTT_RECOVERY.md`.
- Actualizado `docs/INSTALLATION.md` con requisitos y recuperación de resultados existentes.

## [1.0.1] — Documentación de instalación y mantenimiento

**Tipo:** PATCH — corrección compatible de documentación y navegación del proyecto.

### Fixed

- Añadida la guía de instalación que ya era referenciada desde `README.md`.
- Corregidos los enlaces del índice de documentación del README para no apuntar a documentos inexistentes.
- Aclarados los requisitos de Python, dependencias opcionales, FFmpeg, TTS, modelos externos, proveedores de traducción, almacenamiento cloud, ejecución programada y empaquetado.
- Documentado el procedimiento de actualización y la validación de una instalación existente.

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

- `1.1.x` — correcciones compatibles sobre la integración TTS y recuperación.
- `1.2.0` — siguiente conjunto de funcionalidad nueva compatible.
- `2.0.0` — solo ante cambios incompatibles de contrato o arquitectura pública.
