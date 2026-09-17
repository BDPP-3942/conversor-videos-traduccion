# Release Candidate — 1.10.0

## Release

- **Versión:** `1.10.0`
- **Clasificación:** MINOR
- **Baseline publicada anterior:** `v1.9.0`
- **Tag objetivo:** `v1.10.0`
- **Estado:** no publicada; pendiente de CI final, Release Gate y merge a `main`.

## Alcance

`1.10.0` contiene únicamente cambios posteriores a la baseline `v1.9.0`. La aplicación de escritorio, el empaquetado nativo y la automatización inicial de publicación pertenecen a `v1.9.0` y no se vuelven a registrar como novedades de esta release.

### Cambios de producto

- Reparación conservadora de nombres Unicode mal decodificados al extraer ZIP, sin alterar nombres CP437 legítimos.
- Normalización canónica de nombres antes de acceder al filesystem y detección de colisiones por normalización y mayúsculas/minúsculas.
- Separación de las carpetas de trabajo visibles (`input`/`output`) respecto del estado privado de la aplicación.
- Persistencia del estado privado fuera de la carpeta de instalación para facilitar instalaciones nativas y actualizaciones.
- Ampliación de la GUI existente con configuración adicional de Whisper, FFmpeg, traducción local, TTS y archivo de contexto.
- Endurecimiento del instalador Windows para distinguir realmente las arquitecturas x64 y x86.
- Alineación de las opciones públicas de CLI con los parsers reales y sus textos de ayuda.

### Ingeniería de release

- Sincronización reproducible de `uv.lock` mediante una PR auxiliar cuando el cambio de dependencias lo requiere.
- La PR auxiliar se fusiona y se valida automáticamente antes de eliminar su rama.
- La CI del estado resultante se ejecuta explícitamente cuando el cambio de lockfile procede de la automatización.
- `pyproject.toml`, `config/app.toml`, `uv.lock` y los metadatos documentales deben quedar sincronizados en `1.10.0`.

## Compatibilidad

- Los puntos de entrada CLI existentes siguen soportados.
- Se mantiene la ejecución programada/desatendida.
- Siguen disponibles regeneración, subtitle-QA y TTS.
- No se incluye aplicación móvil.
- La capa de escritorio de `v1.9.0` sigue siendo la interfaz gráfica de esta línea; `1.10.0` la amplía, no la sustituye.

## Documentación y CLI

- La documentación operativa nueva o modificada se redacta en español.
- La terminología de programación, librerías, dependencias, APIs, comandos, flags y formatos se conserva cuando es el término técnico establecido.
- Los comentarios y docstrings que contienen texto humano se redactan en español sin eliminar explicaciones técnicas existentes.
- Todas las descripciones `description=` y `help=` de los parsers CLI deben estar en español.
- `docs/CLI.md` debe describir todos los casos de uso públicos y permanecer sincronizado con `--help`.
- Las referencias a otros documentos del repositorio deben ser enlaces Markdown relativos y navegables.
- Las traducciones o reorganizaciones documentales no deben borrar comentarios históricos ni contexto técnico previamente documentado.

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
