# Changelog

## v5.0.0 - reconstructed pipeline

- Reinicio de la línea de versión en `v5.0.0` para la reconstrucción funcional del proyecto.
- Añadidos proveedores de traducción HTTP directos para Google Cloud, DeepL Free y Microsoft Translator F0, con MyMemory como último fallback.
- Añadidos límites de cuota persistentes, reintentos acotados por proveedor y fallback secuencial para segmentos no resueltos.
- Unificada la política de nombres entre ZIP, vídeo directo y reprocesado.
- Añadido procesamiento directo de MP4/MOV/MKV/AVI/WEBM/M4V/WMV sin contenedor ZIP.
- Añadida deduplicación automática local con análisis, plan persistente, dry-run y eliminación conservadora basada en contenido y estabilidad del nombre.
- Mantiene ejecución desatendida, perfiles persistentes de Google Drive/rclone, locks, reprocesado y packaging multiplataforma.
- CI ampliada a Python 3.11/3.12/3.13 con pytest, Ruff, compileall, `pip check` y `pip-audit`.
- Packaging corregido para descubrir todos los subpaquetes `config.*` y `src.*`.

## Unreleased

- Añadida la opción configurable `generate_webm` para omitir la salida secundaria WebM en ejecuciones, builds y tareas programadas; el valor por defecto sigue siendo `true`.
- `reprocess-subtitles` admite ahora ámbito concreto y general: con `--output-folder`, `--video` o `--source` reprocesa una salida; sin selector o con `--all` recorre todas las salidas existentes elegibles.
- La deduplicación de resultados locales se ejecuta automáticamente al finalizar `run`; `--dry-run` se conserva como modo explícito de simulación.
- Añadido `prefetch-whisper` y ajustado PyInstaller para incluir las dependencias cargadas dinámicamente.

## 4.2.3 - Pytest/secondary-video configuration alignment

- Fixed the secondary WebM default mismatch that caused CI to fail: VP9 now defaults to CRF 0, emitting `-lossless 1` as required by the lossless-output policy.
- Synchronized `config/app.toml`, `config/settings.py`, `config/loader.py`, and the performance test with the lossless WebM default.

## 4.1.1 - Ruff compatibility and code-quality cleanup

- Fixed Ruff import ordering, unused imports and modernized Python 3.11 type annotations.
- Replaced deprecated `subprocess` pipe handling with `capture_output` where applicable.
- Preserved duplicate-media detection and context-aware processed-video renaming behavior.

## 4.0.0 - unattended cloud execution

- Google Drive silent OAuth refresh, scheduled execution and persistent provider profiles.
- rclone health checks, isolated configuration and optional managed binary update.
- Cross-platform execution lock and unattended readiness checks.
