# Alcance de release — 1.10.0

## Clasificación

`1.10.0` es la siguiente release **MINOR**. Añade una aplicación de escritorio compatible hacia atrás y una capa de distribución nativa, preservando la CLI, la ejecución programada y los wrappers desatendidos existentes.

La baseline publicada anterior es `v1.8.2`. La documentación histórica de `1.8.x` permanece inmutable; el trabajo histórico de resolución de uv se conserva como contexto y no se reclasifica como parte de esta release.

## Aplicación de escritorio

La release añade el punto de entrada `video-translation-desktop`, implementado como capa de presentación sobre el pipeline existente y no como un segundo motor de procesamiento.

La GUI proporciona:

- procesamiento desde almacenamiento local, Google Drive y rclone;
- selección de idiomas y proveedor de traducción;
- proveedores de respaldo, tamaño de lote y concurrencia de vídeos;
- configuración de modelo, dispositivo, cálculo y beam de Whisper;
- controles de WebM y TTS, incluido TTS obligatorio y voz/velocidad;
- controles de reanudación y normalización de nombres heredados;
- recuperación de subtítulos con modos `full`, `stt_only` y `translate_only`;
- análisis de duplicados, simulación y eliminación confirmada;
- diagnóstico del entorno y preparación de recursos de Whisper;
- eventos de etapa/progreso, ejecución en segundo plano y cancelación cooperativa;
- conservación explícita de la CLI y de la ejecución programada/desatendida.

La autenticación y creación de perfiles de proveedores continúa disponible mediante los flujos CLI/setup establecidos cuando OAuth o rclone requieren credenciales interactivas.

## Arquitectura de control del pipeline

`src/controllable_pipeline.py` adapta el `MediaPipeline` existente con eventos de etapa y cancelación cooperativa. No duplica la lógica audiovisual.

La cancelación se basa deliberadamente en límites seguros: un proceso nativo de FFmpeg o Whisper activo termina su operación actual antes de detener el pipeline. Así se evitan artefactos intermedios corruptos y se mantiene un contrato determinista para la GUI.

## Empaquetado nativo

La release produce artefactos de escritorio nativos mediante PyInstaller y herramientas específicas de cada plataforma:

- **Windows:** ejecutable GUI PyInstaller más MSI WiX 6.
- **macOS:** bundle `.app` de PyInstaller distribuido en ZIP.
- **Linux:** ejecutable PyInstaller dentro de AppDir (`AppRun`, metadata `.desktop` e icono SVG), empaquetado como AppImage x86_64.

La build Windows x64 debe instalarse en el `Program Files` nativo y no en `Program Files (x86)`. Un ejecutable x64 no se presenta como compatible con Windows x86; una variante x86 solo es válida si se construye y valida realmente con Python x86 y dependencias compatibles.

## Automatización de release

Un tag `vX.Y.Z` inicia automáticamente [`.github/workflows/release.yml`](.github/workflows/release.yml). El workflow:

1. comprueba el tag exacto;
2. valida `uv.lock` y prepara el entorno bloqueado;
3. construye los artefactos Linux, Windows y macOS en runners nativos;
4. valida el ejecutable y paquete esperado en cada plataforma;
5. archiva el `.app` de macOS como ZIP;
6. sube los artefactos al workflow;
7. crea la GitHub Release si es necesario y adjunta los binarios.

GitHub continúa proporcionando los archivos fuente asociados al tag. Los artefactos nativos se adjuntan junto a ellos, eliminando la necesidad de builds locales y subidas manuales.

## Consistencia de versión y lockfile

Para `1.10.0`, la versión debe estar sincronizada en:

- [`pyproject.toml`](pyproject.toml);
- [`config/app.toml`](config/app.toml);
- [`uv.lock`](uv.lock);
- [`CHANGELOG.md`](CHANGELOG.md);
- [`docs/RELEASES.md`](docs/RELEASES.md);
- [`docs/VERSIONING.md`](docs/VERSIONING.md);
- [`RELEASE_CANDIDATE.md`](RELEASE_CANDIDATE.md);
- esta especificación y la documentación relacionada de escritorio/release.

El workflow de sincronización de uv puede actualizar el lockfile automáticamente durante la preparación de la PR. El artefacto final debe seguir siendo commitado y validado mediante `uv lock --check`.

## Documentación y CLI

La documentación operativa y los comentarios/docstrings introducidos o modificados deben estar en español. Los nombres de APIs, comandos, opciones CLI, claves de configuración, clases, funciones, rutas y artefactos se conservan literalmente cuando forman parte del contrato.

Las descripciones `description=` y `help=` de todos los parsers CLI deben estar en español. [`docs/CLI.md`](docs/CLI.md) debe recoger todos los casos de uso públicos y mantenerse sincronizado con la salida real de `--help`.

Cuando un documento mencione otro documento del repositorio, debe enlazarlo mediante Markdown relativo. Estas reglas viven en los propios documentos canónicos y no requieren un `INDEX.md` auxiliar.

## CI y Release Gate

La matriz Linux/Windows/macOS con Python 3.11–3.13 sigue siendo obligatoria. El empaquetado de escritorio añade validación nativa en las tres plataformas. El SHA final debe superar tests, lint/formato, compilación, lockfile, empaquetado y Release Gate antes de considerarse publicable.

Las pruebas funcionales y de rendimiento del pipeline y de la aplicación de escritorio son requisitos previos adicionales a la publicación.

La versión móvil queda explícitamente fuera del alcance de `1.10.0`.
