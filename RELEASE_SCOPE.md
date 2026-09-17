# Alcance de release — 1.10.0

## Clasificación

`1.10.0` es la siguiente release **MINOR** respecto de la baseline publicada `v1.9.0`.

La aplicación de escritorio, el empaquetado nativo y la automatización inicial de publicación pertenecen a `v1.9.0`. En `1.10.0` se amplían y endurecen esas capacidades; no se vuelven a contabilizar como funcionalidad nueva de producto.

## Cambios de producto

- Reparación conservadora de nombres Unicode al extraer ZIP, diferenciando UTF-8 mal decodificado de nombres CP437 legítimos.
- Normalización NFC y detección de colisiones de filesystem.
- Endurecimiento de traversal, rutas absolutas/UNC, symlinks y nombres reservados.
- Separación de `input`/`output` visibles y estado privado de la aplicación.
- Ampliación de la GUI existente para configuración de Whisper, FFmpeg, traducción local, TTS, contexto, recuperación, duplicados y diagnóstico.
- Motor Vosk específico para el build Windows x86/32 bits, manteniendo `faster-whisper` en arquitecturas compatibles.
- Alineación de la documentación CLI con los parsers y `--help` reales.
- Conservación de CLI, ejecución programada/headless, wrappers, regeneración, subtitle-QA y TTS.

## Contexto de la aplicación de escritorio

`video-translation-desktop` sigue siendo una capa de presentación sobre el pipeline existente y no un segundo motor de procesamiento.

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

La matriz de publicación validada es:

- **Windows x64:** ejecutable GUI PyInstaller más MSI WiX 6.
- **Windows x86/32 bits:** ejecutable GUI, MSI y wheel `win32`, construidos con Python x86 y `Vosk`.
- **macOS x64:** bundle `.app` de PyInstaller distribuido en ZIP.
- **Linux x86_64:** ejecutable PyInstaller dentro de AppDir, empaquetado como AppImage.

No se anuncia soporte 32-bit para macOS o Linux en `1.10.0`: la cadena actual de Python y las dependencias binarias no permite construir y validar de forma reproducible esos artefactos. Un artefacto de una arquitectura solo se considera soportado cuando la CI lo construye y valida realmente.

La build Windows x64 se instala en el `Program Files` nativo y no en `Program Files (x86)`. Un ejecutable x64 no se presenta como compatible con Windows x86.

## Automatización de release

Un tag `vX.Y.Z` inicia automáticamente [`.github/workflows/release.yml`](.github/workflows/release.yml). El workflow:

1. comprueba el tag exacto;
2. valida `uv.lock` y prepara el entorno bloqueado;
3. construye los artefactos Linux, Windows y macOS en runners nativos;
4. construye además Windows x86 con Python 3.11.9 de 32 bits;
5. valida los ejecutables y paquetes esperados;
6. archiva los bundles portables correspondientes;
7. sube los artefactos al workflow;
8. crea o actualiza la GitHub Release y adjunta los binarios.

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

Las comprobaciones técnicas mantienen sus nombres reales: `Ruff lint`, `Ruff security`, `Ruff format`, `uv lock --check`, `uv sync --locked`, `uv pip check` y `pip-audit`.

Cuando un documento mencione otro documento del repositorio, debe enlazarlo mediante Markdown relativo. No se necesita un `INDEX.md` auxiliar para esa función.

## CI y Release Gate

La matriz Linux/Windows/macOS con Python 3.11–3.13 sigue siendo obligatoria. El empaquetado de escritorio añade validación nativa en las tres plataformas y Windows x86. El SHA final debe superar tests, lint/formato, compilación, lockfile, auditoría de dependencias, empaquetado y Release Gate antes de considerarse publicable.

Las pruebas funcionales de la aplicación de escritorio se validan mediante sus builds nativos y smoke tests de artefactos. TTS se audita mediante su entorno de dependencias y pruebas del pipeline; no se declara soporte para una arquitectura cuyo runtime TTS no pueda instalarse y ejecutarse.

La versión móvil queda fuera del alcance de `1.10.0`.
