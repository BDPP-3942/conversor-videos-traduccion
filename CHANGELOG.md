# Changelog

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

### Security

- Endurecimiento de la ejecución FFmpeg del TTS.
- Restricción de rutas de salida del CLI TTS.
- Auditoría independiente de dependencias TTS.

### Documentation

- Guía funcional y arquitectónica.
- Documentación de instalación, configuración, CLI, STT, TTS, almacenamiento, operación desatendida y seguridad.
- Histórico de releases y política Semantic Versioning.

## Historial anterior

Antes de establecer la línea de releases de producto `1.x`, el repositorio utilizó versiones internas `4.x` y `5.x` durante la reconstrucción y evolución del pipeline. Esas entradas se conservan en el historial Git y en las releases/tag que ya existan, pero no se reinterpretan retroactivamente como versiones `1.x`.

## Próximas versiones

- `1.0.x` — correcciones compatibles, seguridad y documentación.
- `1.1.0` — siguiente conjunto de funcionalidad nueva compatible.
- `2.0.0` — solo ante cambios incompatibles de contrato o arquitectura pública.
