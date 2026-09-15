# Changelog

## [1.10.0] — Endurecimiento Unicode, almacenamiento de runtime y ampliación de la CLI

**Tipo:** MINOR — release candidata.

**Estado:** CANDIDATA — pendiente de CI final, Release Gate, merge a `main` y publicación de `v1.10.0`.

**Baseline:** `v1.9.0` publicada.

### Fixed

- Reparación conservadora de nombres UTF-8 interpretados como CP437 al extraer ZIP, preservando nombres CP437 legítimos.
- Normalización Unicode canónica antes de acceder al filesystem y detección de colisiones por normalización y mayúsculas/minúsculas.
- Separación de las carpetas de trabajo del usuario respecto del estado privado de la aplicación.
- Instalación Windows endurecida para distinguir realmente las arquitecturas x64 y x86.

### Changed

- La GUI de `v1.9.0` amplía la configuración expuesta para Whisper, FFmpeg, traducción local, TTS y archivo de contexto.
- Los puntos de entrada CLI se alinean con los parsers reales y con ayuda pública en español.
- La documentación operativa se traduce al español preservando terminología técnica, comentarios históricos y enlaces relativos.
- La automatización de `uv.lock` utiliza una PR auxiliar cuando procede y valida el estado resultante antes de eliminar su rama.

### Compatibility

- La GUI, el empaquetado nativo y la automatización básica de release introducidos en `v1.9.0` no se vuelven a contabilizar como novedades de `1.10.0`.
- Se mantienen CLI, ejecución unattended/headless, regeneración, subtitle-QA y TTS.
- No se introduce soporte móvil.

## [1.9.0] — Aplicación de escritorio y empaquetado nativo

**Tipo:** MINOR — release candidata publicada como baseline de trabajo de `1.10.0`.

**Estado:** PUBLICADA — tag `v1.9.0`.

**Baseline:** `v1.8.2` publicada.

### Added

- Nueva aplicación GUI multiplataforma mediante `video-translation-desktop`.
- Fachada `VideoTranslationApplication` y adaptador `ControllableMediaPipeline` sobre el `MediaPipeline` existente.
- Eventos de etapa, progreso y cancelación cooperativa en límites seguros, sin duplicar la lógica audiovisual existente.
- GUI para procesamiento, recuperación de subtítulos, gestión de duplicados y diagnósticos.
- Configuración desde GUI de almacenamiento local/Google Drive/rclone, idiomas, proveedor y fallbacks de traducción, concurrencia, parámetros Whisper, WebM, TTS, resume y normalización de nombres.
- Recuperación de resultados existentes en modos `full`, `stt_only` y `translate_only`.
- Herramientas de deduplicación para scan, análisis, dry-run y eliminación con confirmación.
- Diagnósticos para doctor y prefetch de Whisper.

### Packaging

- Windows: ejecutable GUI PyInstaller `.exe` y MSI mediante WiX 6.0.2.
- Windows: ZIP portable con el ejecutable GUI.
- macOS: aplicación GUI `.app` generada por PyInstaller y distribuida en ZIP.
- Linux: GUI PyInstaller encapsulada como AppDir con `AppRun`, metadata `.desktop`, icono SVG y AppImage x86_64.
- Validación de packaging en runners nativos Linux, Windows y macOS.

### Release automation

- Los tags `vX.Y.Z` activan la construcción automática de los artefactos de escritorio.
- Cada plataforma se construye en su runner nativo.
- El workflow valida los artefactos antes de publicarlos.
- AppImage, MSI, ZIP portable de Windows y ZIP de macOS se adjuntan automáticamente a la GitHub Release.
- GitHub continúa generando automáticamente los ZIP/TAR del código fuente asociados al tag.

### Compatibility

- Los entry points CLI existentes permanecen soportados.
- La ejecución unattended/headless y programada mediante los wrappers existentes permanece soportada.
- Regeneración, subtitle-QA y TTS continúan disponibles fuera de la GUI.
- La aplicación de escritorio es una nueva interfaz sobre los casos de uso existentes; no sustituye el pipeline ni crea un segundo motor.
- La cancelación de la GUI es cooperativa y respeta límites seguros.
- No se introduce soporte móvil.

### CI / Validation

- Matriz de tests Linux/Windows/macOS con Python 3.11, 3.12 y 3.13.
- `uv lock --check`, `uv sync --locked`, `uv pip check`, Ruff lint/seguridad/formato y `compileall`.
- Tests de la fachada de aplicación y del pipeline controlable.
- Tests de packaging y smoke validation de artefactos nativos.
- Release Gate antes de publicar `v1.9.0`.

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

**Tipo:** PATCH — release publicada.

**Estado:** PUBLICADA — tag `v1.8.2`.

**Commit/tag de referencia:** `0165f7fdd000c0f29c8a022fa26a452afc55111c` / `v1.8.2`.

### Fixed

- Corregida la revisión fijada de MADLAD-400 3B CT2 INT8 a `fd0b55729c074372eb84b52b9309a00dc65c40c4`.
- Corregido el nombre del tokenizer: el artefacto real es `spiece.model`, no `sentencepiece.model`.
- Conservada la validación de tamaño y SHA-256 de los artefactos gestionados.
- Mejorado el diagnóstico de descargas de Hugging Face para distinguir un `404` de archivo/revisión inexistente de los errores de autenticación/autorización `401/403`.
- Corregidos los fixtures de tests de MADLAD para que los tamaños declarados coincidan con los bytes escritos.
- Alineados los metadatos de aplicación, packaging y documentación con la release `1.8.2`.

### Tests / CI

- Añadidas/regresadas pruebas para la revisión fijada, `spiece.model`, integridad, prefijo de destino MADLAD y diagnóstico de `404`.
- Mantenida cobertura independiente para OPUS-MT y su revisión fijada.
- Release Gate validado antes de publicar `v1.8.2`.

### Compatibility

- Release PATCH compatible sobre `1.8.1`.
- No cambia el pipeline audiovisual ni los contratos públicos de CLI, almacenamiento o formatos.

## [1.8.1] — Local uv Bootstrap & Optional Local Translation Setup

**Tipo:** PATCH — release publicada.

**Estado:** PUBLICADA — tag `v1.8.1`.

- Bootstrap automático de uv multiplataforma, sin requerir una instalación global previa.
- Preparación opcional del modelo local de traducción fijado por el proyecto.
- `uv.lock` y metadatos de proyecto sincronizados con `1.8.1`.
- Regresiones para scripts de instalación y validación CI multiplataforma.

## [1.8.0] — Whisper Recovery & Local Translation

**Tipo:** MINOR — release publicada.

- Recuperación selectiva de segmentos Whisper y separación de silencios VAD/división de subtítulos.
- MADLAD-400 3B CT2 INT8 como modelo local predeterminado, con OPUS-MT como alternativa.
- Validación de integridad y revisiones fijadas de modelos.
- Contexto Whisper para vocabulario de Tai Chi.
- Voz TTS predeterminada `am_michael` y WebM desactivado por defecto.
- Base de desarrollo, CI, build y auditoría con `uv`.

## [1.7.4] — Local translation shared vocabulary validation

**Tipo:** PATCH — release publicada.

- Corregida la validación de `shared_vocabulary.json` para aceptar la estructura real del artefacto fijado.
- Regresiones específicas para vocabulario JSON y descarga/activación del modelo.

## [1.7.3] — Local translation model metadata bootstrap

**Tipo:** PATCH — release publicada.

- Incorporados al paquete los metadatos JSON necesarios para la revisión fijada del modelo local.
- Regresiones de packaging y descarga de artefactos.

## [1.7.2] — Local translation model download fix

**Tipo:** PATCH — release publicada.

- Corregido el límite de descarga de los artefactos del modelo local.
- Corregida la evaluación eager que producía `KeyError: 'model.bin'`.

## [1.7.1] — STT selective recovery compatibility

**Tipo:** PATCH — release publicada.

- Corregido el contrato de `clip_timestamps` de `faster-whisper` para recuperación selectiva.
- Añadidas pruebas de regresión e integración.

## [1.7.0] — Reprocessing, Unicode Naming & Translation Runtime

**Tipo:** MINOR — release publicada.

- Reprocessing de subtítulos y vídeos, manifests atómicos y recuperación de estado.
- Naming determinista y normalización Unicode multiplataforma.
- Endurecimiento de nombres, rutas, colisiones y límites de filesystem.
- Consolidación del proveedor opcional CTranslate2 + SentencePiece y selección conservadora de runtime.

## [1.6.0] — Local Translation & GPU Runtime Hardening

**Tipo:** MINOR — release publicada.

- Traducción local opcional, runtime CUDA gestionado, diagnóstico GPU/CPU y recuperación STT configurable.

## [1.5.1] — ZIP extraction and cross-platform filesystem hardening

**Tipo:** PATCH — release publicada.

- Endurecimiento de extracción ZIP frente a traversal, rutas absolutas, UNC, nombres reservados y colisiones case/Unicode.

## [1.5.0] — Multiplatform Whisper, Context & Packaging

**Tipo:** MINOR — release publicada.

- Dispatcher común para wrappers locales, política de naming/contexto Whisper, CI multiplataforma.

## [1.4.2] — Regeneration CLI contract and help alignment

**Tipo:** MINOR — release publicada.

- Contrato CLI de regeneración y help de regeneración alineados con `MediaPipeline`.

## [1.4.1] — Corrective Script Integration

**Tipo:** PATCH — release publicada.

- Wrappers locales integrados con la regeneración existente sin duplicar lógica.

## [1.4.0] — Clean Video Regeneration and Release Hardening

**Tipo:** MINOR — release publicada.

- Regeneración limpia desde fuente, backup/restauración y endurecimiento de release y packaging.

## [1.3.0] — Safe Resource-Aware Video Concurrency

**Tipo:** MINOR — release publicada.

- Concurrencia automática basada en CPU/RAM/GPU con límites conservadores.

## [1.2.2] — Naming Timestamp Cleanup

**Tipo:** PATCH — release publicada.

- Eliminación de timestamps técnicos de nombres de curso/lección y resultados.

## [1.2.1] — TTS Installation Fix

**Tipo:** PATCH — release publicada.

- Corrección de instalación de assets TTS, especialmente en Windows.

## [1.2.0] — Naming and TTS Improvements

**Tipo:** MINOR — release publicada.

- Naming descriptivo determinista y bootstrap de assets Kokoro.

## [1.1.0] — Reparación de VTT e integración TTS en el pipeline

**Tipo:** MINOR — release publicada.

- Recuperación de VTT inválidos, regeneración controlada y TTS sincronizado en el pipeline común.

## [1.0.1] — Documentación de instalación y mantenimiento

**Tipo:** PATCH — release publicada.

- Añadida la guía de instalación y corregida la navegación documental.

## [1.0.0] — Primera release estable

Primera release estable del producto.
