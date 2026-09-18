# Aplicación de escritorio

La aplicación de escritorio es una capa de presentación sobre `VideoTranslationApplication` y `MediaPipeline`. No duplica la lógica de STT, traducción, TTS, procesamiento multimedia ni almacenamiento.

## Funcionalidad

La GUI expone los casos de uso interactivos del pipeline: procesamiento, recuperación de subtítulos, deduplicación, diagnóstico, preparación de Whisper, modelo local de traducción, WebM, TTS, reanudación, normalización de nombres y selección de archivo de contexto para Whisper. La CLI y la ejecución programada/headless se conservan sin depender de la GUI.

## Carpetas de trabajo y permisos

La aplicación no utiliza `Program Files` como área de datos de trabajo. En Windows, la instalación contiene el ejecutable y recursos de solo lectura; `Documents/Video Translation Pipeline/input` y `output` contienen los datos del usuario y `%LOCALAPPDATA%/VideoTranslationPipeline` contiene estado, logs y cachés. En macOS/Linux se utiliza el equivalente convencional de `Documents` para `input`/`output` y el directorio de datos privado de la aplicación para el estado interno.

Las carpetas de trabajo pueden sustituirse por cualquier ubicación con permisos de escritura, incluidas carpetas compartidas, unidades de red y carpetas sincronizadas.

## Distribución y arquitecturas

Cada artefacto se construye con el intérprete Python y las dependencias de su arquitectura real. No se etiqueta un binario como compatible con una arquitectura que no haya sido construida y validada.

| Plataforma | Arquitectura validada | Artefacto |
| --- | --- | --- |
| Windows | x64 | `.exe` + `.msi` x64 |
| Windows | x86/32 bits | `.exe` + `.msi` x86 y wheel `win32`, mediante `Vosk` para STT |
| macOS | x64 | `.app` dentro de `.zip` |
| Linux | x86_64 | `.AppImage` |

La matriz actual **no declara soporte de 32 bits para macOS ni Linux**. No es correcto fabricar un artefacto x86 cambiando únicamente su nombre: el ecosistema de Python 3.11 y las dependencias binarias actuales del proyecto no proporciona una cadena reproducible para esas dos plataformas. Python 3.11 publica instaladores macOS universal2 de 64 bits, mientras que sí existe un instalador Windows de 32 bits; además, `vosk==0.3.42` publica una wheel `win32`, pero no una wheel macOS de 32 bits ni Linux i686. citeturn3search0turn1search0

Por tanto, la release solo publica arquitecturas que la CI puede construir y validar realmente. Si en el futuro se incorpora un runtime 32-bit completo para Linux o una plataforma macOS 32-bit compatible, deberá añadirse como una nueva matriz de build y una validación funcional independiente.

### Windows

```bash
uv run python scripts/build_desktop.py --clean --version <version> --format windows-msi --windows-arch <x64|x86>
```

`--windows-arch` debe coincidir con la arquitectura del intérprete Python que ejecuta PyInstaller. WiX recibe la misma arquitectura para generar el MSI correspondiente. El x64 se instala en el `Program Files` nativo y la variante x86 utiliza la ubicación de 32 bits correspondiente. El instalador crea un acceso directo en el menú Inicio.

### Linux

```bash
uv run python scripts/build_desktop.py --clean --version <version> --format linux-appimage
```

El artefacto publicado es actualmente `x86_64`; incluye el bundle PyInstaller, `AppRun`, el fichero `.desktop` y el icono SVG.

### macOS

```bash
uv run python scripts/build_desktop.py --clean --version <version> --format native
```

La CI valida el bundle `.app` en macOS x64. La firma y notarización son operaciones de publicación que requieren credenciales de release y no forman parte de cada PR.

## TTS

TTS es opcional. La implementación publicada utiliza `KokoroONNXProvider` con `kokoro-onnx` y los recursos `kokoro-v1.0.onnx` y `voices-v1.0.bin`. La CI comprueba la instalación/auditoría de la dependencia TTS y las pruebas del pipeline verifican la sincronización temporal y la generación del medio. El soporte TTS no debe declararse para una arquitectura cuyo runtime de Python y dependencias no haya sido validado.

## CI/CD

`.github/workflows/desktop.yml` construye los artefactos de Windows x64, Windows x86, macOS x64 y Linux x86_64. El job x86 usa un intérprete Python de 32 bits, comprueba el tamaño de puntero, instala `requirements-x86.txt`, construye el MSI y genera la wheel `win32`.

`.github/workflows/release.yml` repite la matriz sobre el tag exacto y adjunta los artefactos validados a la GitHub Release. No se publica un artefacto x86 que no haya pasado el build correspondiente.

## CLI y ejecución programada

La GUI es una capa adicional. La CLI continúa siendo el contrato de automatización:

```bash
uv run video-translation-pipeline run
uv run video-translation-pipeline run --scheduled
```

También se conservan regeneración, QA de subtítulos, TTS, wrappers desatendidos y programación mediante launchd, cron y el Programador de tareas de Windows.

## Documentación relacionada

- [`README.md`](../README.md)
- [`CLI.md`](CLI.md)
- [`INSTALLATION.md`](INSTALLATION.md)
- [`PACKAGING.md`](PACKAGING.md)
- [`TESTING.md`](TESTING.md)
- [`CI_CD.md`](CI_CD.md)
- [`RELEASES.md`](RELEASES.md)


## Desinstalación y datos de usuario

El instalador MSI mantiene los binarios y recursos de la aplicación separados de los datos escribibles. El estado, las credenciales de proveedor, los modelos descargados y otros recursos gestionados que necesiten escritura se almacenan en la ubicación privada del usuario cuando la aplicación está empaquetada. Las carpetas de entrada y salida permanecen en Documentos.

El instalador incluye `uninstall.cmd` dentro de la carpeta de instalación como acceso directo al desinstalador de Windows Installer. También aparece la entrada normal de Aplicaciones instaladas de Windows. La desinstalación elimina los componentes de la aplicación, pero no elimina automáticamente vídeos, resultados, modelos ni configuración privada del usuario.

La GUI y el núcleo no deben escribir en `Program Files` durante una ejecución normal. Si una ruta configurada explícitamente apunta a una ubicación protegida, esa configuración debe cambiarse a una ubicación con permisos de escritura en lugar de ejecutar la aplicación como administrador.
