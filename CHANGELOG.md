# Changelog

## [1.0.2] — Reparación de VTT y TTS integrado en ejecución

**Tipo:** PATCH — corrección compatible del procesamiento de subtítulos y de la recuperación TTS.

### Fixed

- El STT descarta segmentos degenerados con timestamps no finitos, negativos o con `end <= start` después de la segmentación por silencios.
- Añadida una capa de reparación reutilizable para VTT de STT y VTT traducidos.
- Si el VTT original es inválido, se reutiliza el vídeo ya procesado para regenerar STT y después la traducción.
- Si el VTT original es válido pero el traducido es inválido, se conservan los timestamps originales y solo se vuelve a traducir.
- Si ambos VTT son inválidos, se ejecuta STT una sola vez y se regenera la traducción a partir de los nuevos timestamps.
- Los VTT válidos no se regeneran y el MP4/WebM fuente no se vuelve a crear durante la reparación.
- Los VTT reemplazados se conservan mediante backups antes de aplicar la reparación.
- La generación TTS del pipeline común comprueba y repara los VTT antes de sintetizar audio.
- `TTS_ENABLED=true` mantiene el flujo integrado para ejecuciones locales, programadas y proveedores de almacenamiento soportados mediante el mismo decorador de almacenamiento.

### Documentation

- Añadida `docs/VTT_REPAIR.md` con las reglas de recuperación y las garantías de seguridad del proceso.

## [1.0.1] — Documentación de instalación y mantenimiento

**Tipo:** PATCH — corrección compatible de documentación y navegación del proyecto.

### Fixed

- Añadida la guía de instalación que ya era referenciada desde `README.md`.
- Corregidos los enlaces del índice de documentación del README para no apuntar a documentos inexistentes.
- Aclarados los requisitos de Python, dependencias opcionales, FFmpeg, TTS, modelos externos, proveedores de traducción, almacenamiento cloud, ejecución programada y empaquetado.
- Documentado el procedimiento de actualización y la validación de una instalación existente.

### Documentation

- Nueva `docs/INSTALLATION.md`.
- El índice del README refleja únicamente la documentación que existe actualmente en el repositorio.
- Se mantienen las guías especializadas existentes para TTS, traducción, almacenamiento, ejecución desatendida, deduplicación, seguridad, auditoría y releases.

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
