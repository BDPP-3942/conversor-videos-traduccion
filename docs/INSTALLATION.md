# Instalación y configuración

## Requisitos

- Python 3.11, 3.12 o 3.13 (`>=3.11,<3.14`).
- Acceso a Internet para descargar paquetes, modelos y proveedores cuando corresponda.
- Espacio en disco para medios, recursos de Whisper/TTS y resultados.
- Dependencia opcional de Google para Google Drive.
- `rclone` es un ejecutable externo que el proyecto puede gestionar bajo `tools/rclone/`.

FFmpeg se proporciona mediante `imageio-ffmpeg`, salvo que se configure un ejecutable explícito.

## Instalación

Clona el repositorio y ejecuta el wrapper de configuración:

```bash
git clone https://github.com/BDPP-3942/conversor-videos-traduccion.git
cd conversor-videos-traduccion
chmod +x scripts/setup_env.sh
./scripts/setup_env.sh
```

En Windows:

```bat
scripts\setup_env.bat
```

Los wrappers resuelven `uv` en este orden: copia gestionada existente bajo `tools/uv/`, `uv` disponible en `PATH` y, finalmente, bootstrap oficial bajo `tools/uv/`. La copia local está ignorada por Git y el instalador se ejecuta sin modificar el perfil del shell.

Opciones disponibles:

- `--cloud` — instala el extra de Google Drive.
- `--rclone` — prepara el binario gestionado de rclone.
- `--tts` — instala y habilita Kokoro TTS.
- `--prefetch-whisper` — prepara por adelantado el modelo de Whisper seleccionado.
- `--local-translation` — descarga y valida el modelo local de traducción configurado.

El modelo MADLAD-400 3B predeterminado ocupa aproximadamente 2,95 GB, por lo que `--local-translation` es opt-in. La descarga diferida sigue disponible:

```bash
uv run python scripts/manage_local_translation.py download
uv run python scripts/manage_local_translation.py status
uv run python scripts/benchmark_local_translation.py --sentences 1
```

## Entorno virtual manual

También es válida una instalación manual:

```bash
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows PowerShell
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
```

Los extras `google`, `tts` y `rclone` están declarados en `pyproject.toml`; las dependencias de desarrollo y auditoría son grupos de `uv`.

## Escritorio

La aplicación de escritorio se instala mediante el entry point `video-translation-desktop` o mediante los artefactos de release. La matriz publicada de `1.10.0` valida Windows x64, Windows x86, macOS x64 y Linux x86_64. No se publican artefactos de 32 bits para macOS/Linux porque la cadena de Python y dependencias binaria necesaria no está disponible de forma reproducible para esas plataformas. Python 3.11 publica macOS universal2 de 64 bits y Windows de 32 bits; `vosk==0.3.42` dispone de wheel `win32`. citeturn3search0turn1search0

Para desarrollo:

```bash
uv sync --group dev
uv run video-translation-desktop
```

La aplicación no necesita escribir en `Program Files`. `input` y `output` utilizan carpetas accesibles por el usuario y el estado técnico se mantiene en el directorio privado de datos de la aplicación. Consulta [DESKTOP.md](DESKTOP.md) y [PACKAGING.md](PACKAGING.md).

## NVIDIA/CUDA y Whisper

La aceleración NVIDIA es opcional. `WHISPER_DEVICE=auto` comprueba el driver, el CUDA Toolkit y las librerías de runtime antes de seleccionar CUDA; si no está disponible, utiliza el fallback a CPU. Consulta [CUDA.md](CUDA.md).

## Configuración

La configuración principal está en `config/app.toml`. `.env.example` documenta las sobreescrituras mediante variables de entorno.

```bash
cp .env.example .env
```

No hagas commit de `.env`, credenciales, perfiles de proveedores ni pesos de modelos.

## Contexto de Whisper

`whisper_initial_prompt` acepta texto literal o una ruta a `txt`, `md`, `csv` o `docx`:

```toml
whisper_initial_prompt = "config/palabras_contexto.txt"
```

El contenido del fichero se lee, normaliza y se entrega al motor de Whisper como `initial_prompt`. Esta información actúa como contexto de terminología: favorece que términos presentes en el fichero sean reconocidos con su grafía esperada, pero no constituye una sustitución determinista del decodificador acústico. La GUI permite seleccionar el fichero mediante diálogo.

## Traducción local

La preparación del modelo local valida revisión, tamaño, integridad y estructura antes de activarlo. Los recursos se almacenan bajo `tools/models/translation/` y no se incluyen en los binarios de escritorio.

## TTS

TTS está desactivado por defecto. Cuando se habilita, el proveedor configurado es `KokoroONNXProvider` mediante `kokoro-onnx` y los recursos se preparan con:

```bash
uv sync --extra tts
uv run python scripts/setup_tts.py --enable
```

Los recursos predeterminados son:

```text
tools/tts/kokoro-v1.0.onnx
tools/tts/voices-v1.0.bin
```

Las rutas pueden personalizarse mediante `TTS_MODEL_PATH` y `TTS_VOICES_PATH`. La funcionalidad TTS se considera soportada en una arquitectura solo cuando `kokoro-onnx`, ONNX Runtime y los recursos correspondientes pueden instalarse y ejecutarse en esa arquitectura.

## Google Drive y rclone

```bash
uv run python main.py provider setup-google --help
uv run python main.py provider bootstrap
uv run python main.py provider setup-rclone --help
```

Las credenciales y la configuración de rclone se mantienen fuera del código fuente.

## Validación de la instalación

```bash
uv run python main.py doctor
uv run python main.py --help
uv run python main.py run --help
uv run python main.py reprocess-subtitles --help
uv run python main.py run --dry-run
```

Para desarrollo:

```bash
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
uv run python -m compileall .
```

## Primera ejecución

Coloca un vídeo o ZIP compatible en `storage/input/` y ejecuta:

```bash
uv run python main.py run
```

Los wrappers equivalentes son `scripts/run_local.sh` y `scripts\run_local.bat`.

## Resultados existentes

No reintroduzcas fuentes ya procesadas sin revisar el estado existente. Utiliza los workflows de duplicados y recuperación cuando corresponda:

```bash
uv run python main.py duplicates scan
uv run python main.py duplicates analyze
uv run python main.py reprocess-subtitles --help
```

Consulta [RESUME.md](RESUME.md) y [SUBTITLES.md](SUBTITLES.md).

## Limpieza

Los recursos gestionados pueden inspeccionarse o limpiarse independientemente:

```bash
uv run python scripts/manage_runtime_resources.py translation-model status
uv run python scripts/manage_runtime_resources.py translation-model cleanup
uv run python scripts/manage_runtime_resources.py cuda status
uv run python scripts/manage_runtime_resources.py cuda cleanup
```

Estos comandos no eliminan `storage/`, manifests, código fuente ni credenciales. Para eliminar el `uv` gestionado por el proyecto basta con borrar `tools/uv/`.

## Actualización

1. Detén la ejecución programada.
2. Haz una copia de seguridad de `storage/output`, `storage/archive`, `storage/state`, manifests y perfiles.
3. Actualiza el código con `git pull`.
4. Ejecuta de nuevo el wrapper de configuración si cambió el grafo de dependencias.
5. Ejecuta `uv run python main.py doctor` y `uv run python main.py run --dry-run`.
6. Prueba una entrada representativa.
7. Vuelve a habilitar la programación.

No elimines manifests ni resultados durante una actualización salvo que una migración documentada lo requiera.
