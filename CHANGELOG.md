# Changelog

## [1.10.0] — Aplicación de escritorio, empaquetado nativo y endurecimiento Unicode

**Tipo:** MINOR — release candidata.

**Estado:** CANDIDATA — pendiente de CI final, Release Gate, merge a `main` y publicación de `v1.10.0`.

**Baseline:** `v1.8.2` publicada.

### Added

- Nueva aplicación GUI multiplataforma mediante `video-translation-desktop`.
- Fachada `VideoTranslationApplication` y adaptador `ControllableMediaPipeline` sobre el `MediaPipeline` existente.
- Eventos de etapa, progreso y cancelación cooperativa en límites seguros, sin duplicar la lógica audiovisual existente.
- GUI para procesamiento, recuperación de subtítulos, gestión de duplicados y diagnósticos.
- Configuración desde GUI de almacenamiento local/Google Drive/rclone, idiomas, proveedor y fallbacks de traducción, concurrencia, parámetros Whisper, WebM, TTS, resume y normalización de nombres.
- Selección de archivo de contexto para el prompt inicial de Whisper.
- Recuperación de resultados existentes en modos `full`, `stt_only` y `translate_only`, incluyendo recuperación individual y global.
- Reparación conservadora de nombres UTF-8 mal decodificados como CP437 al extraer ZIP, preservando nombres CP437 legítimos.
- Separación de las carpetas de trabajo del usuario respecto del estado privado de la aplicación.

### Packaging

- Windows: ejecutable GUI PyInstaller `.exe` y MSI mediante WiX 6.0.2.
- Windows x64: instalación en el `Program Files` nativo; no se presenta un ejecutable x64 como compatible con Windows x86.
- Windows: ZIP portable con el ejecutable GUI para distribución sin instalador.
- macOS: aplicación GUI `.app` generada por PyInstaller y distribuida en ZIP.
- Linux: la misma GUI PyInstaller se encapsula como AppDir con `AppRun`, metadata `.desktop` e icono SVG y se publica como AppImage x86_64.
- Validación de packaging en runners nativos Linux, Windows y macOS.

### Release automation

- Los tags `vX.Y.Z` activan automáticamente la construcción de los artefactos de escritorio.
- Cada plataforma se construye en su runner nativo, evitando builds cruzados no soportados.
- El workflow valida los artefactos antes de publicarlos.
- AppImage, MSI, ZIP portable de Windows y ZIP de macOS se adjuntan automáticamente a la GitHub Release.
- GitHub continúa generando automáticamente los ZIP/TAR del código fuente asociados al tag.
- Se elimina el proceso manual de build, empaquetado y subida de binarios en cada release.

### Compatibility

- Los entry points CLI existentes permanecen soportados.
- La ejecución unattended/headless y programada mediante los wrappers existentes permanece soportada.
- Regeneración, subtitle-QA y TTS continúan disponibles fuera de la GUI.
- La aplicación de escritorio es una nueva interfaz sobre los casos de uso existentes; no sustituye el pipeline ni crea un segundo motor de procesamiento.
- La cancelación de la GUI es cooperativa y respeta límites seguros; no fuerza la terminación de FFmpeg o Whisper en mitad de una operación.
- Las descripciones `description=` y `help=` de los parsers CLI de esta línea de trabajo deben permanecer en español.
- No se introduce soporte móvil en esta release.

### Documentation

- La documentación operativa nueva o modificada se mantiene en español.
- Las referencias entre documentos se expresan mediante enlaces Markdown relativos.
- Los comandos de ejemplo explican su propósito y efecto, no solo su sintaxis.
- `docs/CLI.md` mantiene el contrato de uso público y se sincroniza con la salida real de `--help`.
- Los comentarios y docstrings modificados conservan las explicaciones técnicas en español.

### CI / Validation

- Matriz de tests Linux/Windows/macOS con Python 3.11, 3.12 y 3.13.
- `uv lock --check`, `uv sync --locked`, `uv pip check`, Ruff lint/seguridad/formato y `compileall`.
- Tests de la fachada de aplicación, pipeline controlable y reparación de nombres ZIP.
- Tests de packaging y smoke validation de artefactos nativos.
- Pruebas funcionales y de rendimiento de la aplicación de escritorio y del pipeline antes de publicar.
- Release Gate antes de publicar `v1.10.0`.

## [1.8.3] — Release candidate

**Tipo:** PATCH — release candidata.

**Estado:** CANDIDATA — corrección multiplataforma del mecanismo de resolución de `uv`, pendiente de CI/Release Gate y publicación del tag `v1.8.3`.

**Baseline publicado:** `v1.8.2`. Esta release añade exclusivamente la corrección de resolución de `uv` en los consumidores del bootstrap gestionado por el proyecto.

### Fixed

- Añadido un resolvedor POSIX compartido que prioriza `tools/uv/uv` y usa `uv` de `PATH` como fallback.
- Añadido el resolvedor Windows equivalente, que prioriza `tools\\uv\\uv.exe` antes de `PATH`.
- Corregidos `run_local.*`, `run_unattended.*`, `setup_rclone.*`, `setup_google.*` y los scripts de build para consumir el ejecutable resuelto.
- Conservada la prioridad de ejecutables empaquetados en los wrappers unattended y el fallback directo a `.venv` Python cuando uv no está disponible.
- Eliminada la dependencia accidental de una instalación global de uv para ejecutar un checkout correctamente preparado por `setup_env.*`.

### Tests / CI

- Añadida `tests/test_uv_resolution_contract.py` con cobertura de los contratos POSIX y Windows.
- Verificada la precedencia de `tools/uv/` sobre `PATH`.
- Verificado que los wrappers y builds no vuelvan a exigir `command -v uv` o `where uv.exe` como precondición global.
- Conservada la matriz CI Linux/Windows/macOS y Python 3.11/3.12/3.13.

### Documentation

- Añadida la documentación específica de la resolución compartida de `uv` sin eliminar el historial de releases anteriores.
- Documentado el límite de versión que impide publicar la nueva aplicación de escritorio dentro de `1.8.3`.

### Compatibility

- PATCH compatible con la línea `1.8.x`.
- No cambia el pipeline audiovisual ni los contratos públicos de CLI, almacenamiento o formatos.

## [1.8.2] — MADLAD model download and Hugging Face revision fix
