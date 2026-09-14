# Versionado

La línea de releases de producto es `1.x` y utiliza Semantic Versioning.

## Releases publicadas

- `v1.8.2` — PATCH: corrección de la revisión MADLAD, tokenizer, fixtures e información de diagnóstico de Hugging Face.
- `v1.8.1` — PATCH: bootstrap gestionado de uv y preparación opt-in de traducción local.
- `v1.8.0` — MINOR: recuperación Whisper refinada, modelos locales fijados y base reproducible con uv.
- `v1.7.4` — PATCH: validación de `shared_vocabulary.json` y migración reproducible a uv.
- `v1.7.3` — PATCH: bootstrap de metadatos JSON del modelo local.
- `v1.7.2` — PATCH: corrección de descarga del modelo local.
- `v1.7.1` — PATCH: compatibilidad de recuperación selectiva STT con `clip_timestamps`.
- `v1.7.0` — MINOR: reprocessing, manifests, naming Unicode/filesystem y runtime de traducción local.
- `v1.6.0` — MINOR: traducción local, recuperación STT configurable y endurecimiento GPU/runtime.
- `v1.5.1` — PATCH: endurecimiento ZIP/filesystem multiplataforma.
- `v1.5.0` — MINOR: wrappers multiplataforma, contexto Whisper y packaging.
- `v1.4.2` — PATCH: contrato CLI y help de regeneración.
- `v1.4.1` — PATCH: integración de regeneración en wrappers.
- `v1.4.0` — MINOR: regeneración limpia y endurecimiento de release.
- `v1.3.0` — MINOR: concurrencia adaptativa por recursos.
- `v1.2.2` — PATCH: limpieza de timestamps en naming.
- `v1.2.1` — PATCH: instalación multiplataforma de recursos TTS.
- `v1.2.0` — MINOR: naming descriptivo y bootstrap TTS.
- `v1.1.0` — MINOR: reparación VTT y TTS sincronizado.
- `v1.0.1` — PATCH: documentación inicial de instalación y mantenimiento.
- `v1.0.0` — primera release estable.

Los tags publicados son historia inmutable.

## Release candidate: 1.9.0

`1.9.0` es una **MINOR** porque introduce una capacidad nueva y compatible: una aplicación GUI de escritorio y su distribución nativa.

### Cambios registrados en 1.9.0

1. **Aplicación de escritorio:** nuevo entry point `video-translation-desktop` y GUI Tk/ttk multiplataforma.
2. **Arquitectura:** `VideoTranslationApplication` centraliza la fachada de aplicación y `ControllableMediaPipeline` adapta el pipeline existente para eventos de etapa y cancelación cooperativa.
3. **Procesamiento GUI:** almacenamiento local/Google Drive/rclone, idiomas, proveedores/fallbacks, concurrencia, Whisper, WebM, TTS, resume y normalización de nombres.
4. **Recuperación:** workflows `full`, `stt_only` y `translate_only`.
5. **Deduplicación:** scan, análisis, dry-run y eliminación confirmada.
6. **Diagnóstico:** comprobaciones del entorno y preparación de Whisper.
7. **UX:** ejecución en segundo plano, barra de progreso, log, estado, errores y cancelación segura en límites de etapa.
8. **Windows:** PyInstaller `.exe` y MSI WiX 6.0.2.
9. **macOS:** bundle `.app`, archivado automático como `.zip`.
10. **Linux:** PyInstaller executable + AppDir + `AppRun` + `.desktop` + SVG + AppImage x86_64.
11. **CI/CD:** validación nativa en Linux/Windows/macOS y workflow de release activado por tags.
12. **Release assets:** los binarios se generan automáticamente y se adjuntan a GitHub Release; los ZIP fuente siguen siendo los archivos automáticos del tag.
13. **CLI:** los entry points existentes y la ejecución programada/headless permanecen soportados.
14. **Alcance:** móvil permanece fuera de esta release.

## Política de dependencias

`pyproject.toml` es la fuente declarativa. `uv.lock` es la resolución reproducible versionada y debe estar sincronizada con cada versión publicada. `uv lock --check` y `uv sync --locked` forman parte del Release Gate.

## Trazabilidad

```text
pyproject.toml / config/app.toml
          ↓
      uv.lock
          ↓
     CHANGELOG.md
          ↓
  docs/RELEASES.md
          ↓
 Release Gate + CI
          ↓
   validated main SHA
          ↓
       tag vX.Y.Z
          ↓
 GitHub Release + desktop artifacts
```

La release automática de escritorio se ejecuta desde `.github/workflows/release.yml` cuando se crea un tag `vX.Y.Z`. El workflow construye los artefactos en runners nativos y los adjunta al GitHub Release. No se deben subir manualmente binarios generados desde un equipo de desarrollo.

## Semantic Versioning

- **MAJOR:** cambios incompatibles de CLI, configuración, formatos o contratos públicos.
- **MINOR:** funcionalidad nueva compatible hacia atrás.
- **PATCH:** correcciones compatibles, seguridad, documentación y mantenimiento.
