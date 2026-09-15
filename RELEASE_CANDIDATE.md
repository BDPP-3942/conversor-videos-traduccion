# Release Candidate — 1.10.0

## Release

- **Versión:** `1.10.0`
- **Clasificación:** MINOR
- **Baseline publicada anterior:** `v1.8.2`
- **Tag objetivo:** `v1.10.0`
- **Estado:** no publicada; pendiente de CI final, Release Gate y merge a `main`.

## Alcance

`1.10.0` introduce la aplicación de escritorio y la capa de distribución nativa descritas en [`docs/DESKTOP.md`](docs/DESKTOP.md) y [`RELEASE_SCOPE.md`](RELEASE_SCOPE.md).

### Cambios de producto

- Nuevo punto de entrada `video-translation-desktop`.
- Pestañas GUI para procesamiento, recuperación de subtítulos, gestión de duplicados, diagnóstico y orientación sobre CLI/programación.
- Reutilización del `MediaPipeline` existente mediante `VideoTranslationApplication` y `ControllableMediaPipeline`.
- Eventos de progreso por etapa y cancelación cooperativa en límites seguros.
- Configuración desde la GUI de proveedores de almacenamiento, idiomas, proveedores/fallbacks de traducción, concurrencia, Whisper, WebM, TTS, reanudación y comportamiento de nombres.
- Modos de recuperación `full`, `stt_only` y `translate_only`.
- Flujos de análisis/eliminación de duplicados con simulación y confirmación.
- Reparación conservadora de nombres Unicode mal decodificados al extraer ZIP.
- Selección de archivo de contexto para el prompt inicial de Whisper.

### Cambios de empaquetado

- Bundle de escritorio mediante PyInstaller.
- Ejecutable Windows `.exe` y MSI mediante WiX 6.
- Aplicación macOS `.app`.
- AppImage Linux x86_64 generado desde el ejecutable PyInstaller más AppDir.
- Validación nativa del empaquetado en Linux, Windows y macOS.
- El build de escritorio recibe explícitamente la versión de release y no mantiene una versión 1.9.0 fija.

### Ingeniería de release

- El workflow de GitHub Release activado por tags construye los artefactos nativos en runners nativos y los adjunta a la release.
- Los archivos fuente continúan siendo los archivos generados automáticamente por GitHub a partir del tag.
- El proceso normal de release no requiere build ni subida manual.
- `pyproject.toml`, `config/app.toml`, `uv.lock` y los metadatos documentales deben quedar sincronizados en `1.10.0`.

## Compatibilidad

- Los puntos de entrada CLI existentes siguen soportados.
- Se mantiene la ejecución programada/desatendida.
- Siguen disponibles regeneración, subtitle-QA y TTS.
- No se incluye aplicación móvil.
- La capa de escritorio es aditiva y no sustituye el pipeline existente.

## Documentación y CLI

- La documentación operativa nueva o modificada debe redactarse en español.
- Las explicaciones y comentarios de código introducidos o modificados para esta release deben estar en español; nombres técnicos, flags, claves de configuración y APIs conservan su forma literal.
- Todas las descripciones `description=` y `help=` de los parsers CLI deben estar en español.
- `docs/CLI.md` debe describir todos los casos de uso públicos y permanecer sincronizado con `--help`.
- Las referencias a otros documentos del repositorio deben ser enlaces Markdown relativos y navegables.
- Las reglas anteriores forman parte de los propios documentos canónicos; no se mantiene un índice auxiliar como especificación de cambios.

## Validación requerida antes de publicar

- Linux, Windows y macOS.
- Python 3.11, 3.12 y 3.13.
- Suite completa de pytest.
- Ruff lint, ordenación de imports y formato.
- `uv lock --check` y `uv sync --locked`.
- `uv pip check` y validación de empaquetado.
- Builds nativos de escritorio y smoke tests de artefactos en los sistemas objetivo.
- Pruebas funcionales y de rendimiento del pipeline y de la aplicación de escritorio.
- Release Gate sobre el SHA final exacto.

## Regla de publicación

Crear `v1.10.0` únicamente desde el SHA final exacto que haya superado toda la validación en `main`. Una vez creado el tag, [`.github/workflows/release.yml`](.github/workflows/release.yml) construirá y adjuntará automáticamente los artefactos de escritorio.
