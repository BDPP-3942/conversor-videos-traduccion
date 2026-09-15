# Instalación y configuración

## Requisitos

- Python 3.11, 3.12 o 3.13 (`>=3.11,<3.14`). Los scripts de configuración pueden instalar la versión de Python solicitada mediante la herramienta `uv` gestionada por el proyecto.
- Acceso a Internet para descargar paquetes/modelos/proveedores cuando corresponda.
- Espacio en disco para medios, recursos de Whisper/TTS y salidas generadas.
- Dependencia opcional de Google para Google Drive.
- rclone es un ejecutable externo; el proyecto puede hacer bootstrap y gestionar su propio binario bajo `tools/rclone/`.

FFmpeg se proporciona mediante la dependencia `imageio-ffmpeg`, salvo que se configure un ejecutable explícito.

## Instalación

Clona el repositorio:

```bash
git clone https://github.com/BDPP-3942/conversor-videos-traduccion.git
cd conversor-videos-traduccion
```

### macOS/Linux

```bash
chmod +x scripts/setup_env.sh
./scripts/setup_env.sh
```

El script de configuración utiliza primero el ejecutable `tools/uv/uv` gestionado por el proyecto cuando ya existe. En caso contrario utiliza `uv` desde `PATH`; si ninguno está disponible, descarga el instalador oficial de uv y crea la copia gestionada por el proyecto bajo `tools/uv/`. El binario local está ignorado por Git y el instalador se ejecuta en modo no gestionado, por lo que la configuración no modifica el perfil de shell del usuario.

El script de configuración acepta estas opciones opcionales:

- `--cloud` — instala el extra de Google Drive.
- `--rclone` — hace bootstrap del binario gestionado de rclone.
- `--tts` — instala y habilita la dependencia/recursos opcionales de Kokoro TTS.
- `--prefetch-whisper` — descarga por adelantado el modelo de Whisper seleccionado por la aplicación.
- `--local-translation` — descarga y valida el modelo de traducción local fijado y configurado durante la misma ejecución de configuración.

Para una configuración local completa, incluido el modelo de traducción MADLAD-400 3B predeterminado:

```bash
./scripts/setup_env.sh --local-translation
```

La opción `--local-translation` es deliberadamente opt-in porque el modelo MADLAD predeterminado ocupa aproximadamente 2,95 GB. Si se omite, el entorno queda completamente preparado, pero no se descargan los pesos de traducción local. Pueden instalarse posteriormente con el comando existente:

```bash
uv run python scripts/manage_local_translation.py download
```

El estado y un benchmark real del runtime pueden comprobarse con:

```bash
uv run python scripts/manage_local_translation.py status
uv run python scripts/benchmark_local_translation.py --sentences 1
```

El binario `uv` gestionado por el proyecto no se incluye en el repositorio. Se descarga para la plataforma anfitriona cuando es necesario, mientras que el entorno de Python sigue siendo el `.venv` normal del proyecto gestionado por uv.

### Windows

```bat
scripts\setup_env.bat
```

El script de configuración de Windows implementa el mismo orden de resolución de uv y descarga `tools\uv\uv.exe`, gestionado por el proyecto, cuando no hay disponible un `uv.exe` del sistema. Acepta las mismas seis opciones opcionales indicadas anteriormente.

### Entorno virtual manual

Los scripts de configuración son la vía de instalación preferida porque hacen bootstrap de uv cuando es necesario. Sigue siendo compatible una instalación manual:

```bash
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows PowerShell
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
```

Los extras opcionales se declaran en `pyproject.toml`. El repositorio define actualmente los extras `google`, `tts` y `rclone`; las dependencias de desarrollo, auditoría y empaquetado son grupos de dependencias de uv:

```bash
python -m pip install -e ".[google]"
python -m pip install -e ".[tts]"
uv sync --group dev
uv sync --group audit
```

## Release 1.8.1

`1.8.1` es la siguiente release PATCH después de la publicada `1.8.0`. Mejora la configuración desde un checkout limpio haciendo que uv pueda hacer bootstrap cuando no existe un uv del sistema, añade una opción explícita de un solo comando para preparar el modelo de traducción local fijado y conserva el comando independiente de descarga del modelo para una instalación aplazada.

Los rangos de dependencias del runtime siguen siendo `faster-whisper>=1.2.1,<1.3` y `ctranslate2>=4.8.2,<4.9`.

## NVIDIA/CUDA y Whisper

La aceleración NVIDIA es opcional. La release `1.8.1` no cambia la arquitectura del runtime GPU consolidada en las releases anteriores; la ruta GPU requiere CUDA 12, cuBLAS para CUDA 12 y cuDNN 9 para CUDA 12.

`WHISPER_DEVICE=auto` no considera suficiente la presencia de `nvidia-smi`. Durante la inicialización de Whisper, el proyecto comprueba el driver NVIDIA, busca un CUDA Toolkit instalado, comprueba las librerías de runtime NVIDIA requeridas y pregunta a CTranslate2 si realmente están disponibles un dispositivo CUDA y tipos de cálculo compatibles.

Si se detecta una GPU NVIDIA pero el runtime está incompleto, una ejecución interactiva muestra las versiones detectadas, los requisitos, la ubicación aproximada de instalación y el motivo del fallo, y pregunta si debe instalarse el runtime NVIDIA gestionado. Las librerías gestionadas se colocan bajo `tools/cuda/python/`; el driver NVIDIA no se sustituye y esta operación no instala un CUDA Toolkit completo. En ejecución desatendida no se muestra ningún aviso de instalación y se utiliza el fallback existente a CPU.

Un CUDA Toolkit instalado globalmente no se sustituye ni elimina automáticamente. Puede utilizarse cuando sea compatible, mientras que el runtime gestionado puede proporcionar las librerías de espacio de usuario requeridas sin modificar el Toolkit global.

Consulta [`docs/CUDA.md`](CUDA.md) para diagnóstico, compatibilidad y limpieza.

## Configuración

La configuración predeterminada está en `config/app.toml`. `.env.default` proporciona valores de entorno predeterminados y `.env.example` documenta las sobreescrituras mediante variables de entorno.

```bash
cp .env.example .env
```

En Windows:

```bat
copy .env.example .env
```

No hagas commit de `.env`, credenciales, perfiles de proveedores ni pesos de modelos.

## Nombres y migración de salidas existentes

La política de nombres forma parte del núcleo de la aplicación y no es una opción de instalación. Separa los metadatos lógicos de curso/recurso de los nombres físicos del sistema de archivos.

La forma física es:

```text
<curso_o_contenedor>x<nombre_sanitizado>
```

`x` es el separador de ámbito y `_` el separador de palabras. Los nombres físicos normalizan espacios y guiones separadores, puntuación y controles incompatibles, diacríticos Unicode, nombres reservados de Windows y límites de longitud del sistema de archivos. La migración de salidas existentes se controla mediante el ajuste de workflow `normalize_legacy_names` y está diseñada para conservar el contenido mientras mueve únicamente las rutas de salida afectadas.

## Directorios de runtime

La estructura del runtime es:

```text
storage/
├── input/
├── work/
├── output/
│   └── _manifests/
├── archive/
├── failures/
├── logs/
└── state/
```

Si un checkout no contiene algún directorio, créalo bajo `storage/`; los logs se escriben en `storage/logs/pipeline.log`.

Los recursos opcionales de modelos/runtime gestionados se mantienen bajo `tools/` y están deliberadamente separados de los datos del proyecto. El ejecutable uv gestionado por el proyecto, cuando se hace bootstrap, reside bajo `tools/uv/` y está ignorado por Git.

## Proveedores de traducción

La configuración de procesamiento predeterminada utiliza el proveedor declarado en `config/app.toml` (actualmente Mistral en la referencia del repositorio) con la cadena de fallback configurada. Las credenciales de los proveedores se configuran mediante mecanismos de entorno/perfiles. Consulta [TRANSLATION_PROVIDERS.md](TRANSLATION_PROVIDERS.md).

Para el proveedor local offline opcional, la vía de configuración preferida es ahora:

```bash
./scripts/setup_env.sh --local-translation
```

Esa opción ejecuta el mismo flujo de descarga validada que el gestor independiente después de preparar el entorno de Python. Utiliza el modelo fijado configurado por el checkout; el predeterminado es MADLAD-400 3B CT2 INT8. Si prefieres aplazar la descarga del modelo grande, omite la opción y ejecútala posteriormente:

```bash
uv run python scripts/manage_local_translation.py download
```

La preparación del modelo local valida el modelo fijado seleccionado antes de activarlo. MADLAD requiere `model.bin`, `sentencepiece.model`, `config.json` y `shared_vocabulary.json`; OPUS-MT conserva su contrato de `model.bin`, `source.spm`, `target.spm` y metadatos JSON. La instalación de MADLAD está limitada por el presupuesto de instalación del proyecto y la integridad del modelo se comprueba antes del uso offline.

El modelo se almacena bajo `tools/models/translation/`. Consulta [LOCAL_TRANSLATION.md](LOCAL_TRANSLATION.md).

Después de descargarlo, valida el runtime real en lugar de comprobar únicamente la presencia de archivos:

```bash
uv run python scripts/manage_local_translation.py status
uv run python scripts/benchmark_local_translation.py --sentences 1
```

El benchmark inicializa CTranslate2 + SentencePiece y ejecuta una traducción real con el modelo preparado.

## TTS

TTS está desactivado de forma predeterminada. Cuando se habilita, el proveedor local es Kokoro mediante `kokoro-onnx`. El helper de configuración prepara los recursos predeterminados cuando TTS está habilitado:

```text
tools/tts/kokoro-v1.0.onnx
tools/tts/voices-v1.0.bin
```

Instalación explícita equivalente:

```bash
python -m pip install -e ".[tts]"
python scripts/setup_tts.py --enable
```

Las ubicaciones personalizadas de recursos pueden configurarse mediante `TTS_MODEL_PATH` y `TTS_VOICES_PATH`.

## Google Drive y rclone

Google Drive requiere el extra `[google]` y un perfil de proveedor. La configuración interactiva se expone mediante:

```bash
uv run python main.py provider setup-google --help
```

rclone no es una dependencia de Python. El proyecto puede hacer bootstrap de su binario gestionado de rclone y después configurar un remote mediante la CLI del proveedor:

```bash
uv run python main.py provider bootstrap
uv run python main.py provider setup-rclone --help
```

El binario gestionado se almacena bajo `tools/rclone/`; su configuración está bajo `secrets/rclone/rclone.conf` de forma predeterminada.

## Validar la instalación

```bash
uv run python main.py doctor
uv run python main.py --help
uv run python main.py run --help
uv run python main.py reprocess-subtitles --help
uv run python main.py run --dry-run
```

Para comprobaciones de desarrollo:

```bash
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
uv run python -m compileall .
```

## Primera ejecución

Para procesamiento local, coloca un vídeo o ZIP compatible en `storage/input/` y ejecuta:

```bash
uv run python main.py run
```

Los wrappers equivalentes son `scripts/run_local.sh` y `scripts\run_local.bat`.

## Resultados existentes

No vuelvas a introducir a ciegas fuentes ya procesadas. Inspecciona la salida existente y utiliza los workflows de duplicados/recuperación de subtítulos cuando corresponda:

```bash
uv run python main.py duplicates scan
uv run python main.py duplicates analyze
uv run python main.py reprocess-subtitles --help
```

Consulta [RESUME.md](RESUME.md) y [SUBTITLES.md](SUBTITLES.md).

## Limpieza y desinstalación

Los recursos gestionados por el proyecto pueden inspeccionarse o eliminarse de forma independiente:

```bash
uv run python scripts/manage_runtime_resources.py translation-model status
uv run python scripts/manage_runtime_resources.py translation-model cleanup
uv run python scripts/manage_runtime_resources.py cuda status
uv run python scripts/manage_runtime_resources.py cuda cleanup
```

Estos comandos no eliminan los datos de `storage/`, el código fuente, los manifests ni las credenciales. La limpieza de CUDA solo elimina el directorio `tools/cuda/` del proyecto; no desinstala un driver NVIDIA global ni un CUDA Toolkit global. Consulta [UNINSTALLATION.md](UNINSTALLATION.md).

Si es necesario eliminar la herramienta uv gestionada por el proyecto, borra `tools/uv/`; esto no afecta a un uv del sistema instalado por separado.

## Actualización

1. Detén la ejecución programada.
2. Haz una copia de seguridad de `storage/output`, `storage/archive`, `storage/state`, manifests y perfiles de proveedores.
3. Actualiza el código fuente con `git pull`.
4. Vuelve a ejecutar `./scripts/setup_env.sh` (o `scripts\setup_env.bat`) si cambió el grafo de dependencias o el comportamiento de configuración.
5. Ejecuta `uv run python main.py doctor` y `uv run python main.py run --dry-run`.
6. Prueba una entrada representativa.
7. Vuelve a habilitar la programación.

No elimines manifests ni salidas durante una actualización salvo que una migración documentada lo requiera.

## Empaquetado

El repositorio proporciona actualmente scripts de empaquetado para Windows y Linux:

```bash
uv sync --group dev --extra tts
./scripts/build_linux.sh
```

Windows:

```bat
uv sync --group dev --extra tts
scripts\build_windows.bat
```

Actualmente no existe un script de empaquetado del repositorio para macOS. Consulta [PACKAGING.md](PACKAGING.md).
