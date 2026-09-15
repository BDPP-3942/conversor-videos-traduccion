# Migración a UV — vista previa histórica

Este documento se conserva como registro histórico de diseño de la migración desde el workflow de desarrollo basado en pip/requirements hacia `uv`. La migración se implementó mediante la PR #42 y ya está integrada en `main`; forma parte de la línea base publicada `1.7.4`. El documento ya no es una propuesta ni una migración de producción pendiente.

## Arquitectura objetivo

```text
pyproject.toml
  ├─ dependencias de runtime
  ├─ extras opcionales: google / tts / package
  └─ grupo de dependencias dev
          │
          ▼
       uv.lock
          │
          ├─ .venv local
          ├─ CI: uv sync --locked
          └─ empaquetado: uv build
                    │
                    ▼
                dist/*.whl
                    │
                    ▼
          gate de instalación pip limpia
```

`pyproject.toml` sigue siendo la fuente declarativa. `uv.lock` se convierte en el grafo de dependencias resuelto y reproducible y debe incluirse en el repositorio una vez implementada la migración. Las wheels publicadas siguen siendo wheels estándar de Python y deben continuar instalándose con pip; los usuarios finales no deben estar obligados a instalar uv.

## Vista previa histórica implementada por la PR #42

El workflow histórico `.github/workflows/uv-preview.yml` demostraba la secuencia de CI prevista antes de la migración de producción. El workflow actual autoritativo es `.github/workflows/ci.yml`.

1. Instalar una release controlada de la action de uv.
2. Preparar Python mediante uv.
3. Resolver el grafo de dependencias.
4. Sincronizar el entorno de desarrollo con los extras del proyecto.
5. Ejecutar comprobaciones de dependencias, pruebas, Ruff y empaquetado mediante uv.
6. Instalar la wheel resultante con pip en un entorno limpio y ejecutar las comprobaciones existentes de compatibilidad de puntos de entrada.

La migración ya está completa: `uv.lock` está versionado y la CI actual utiliza `uv lock --check` y sincronización bloqueada. El uso restante de pip es deliberado para la compatibilidad de wheels limpias y determinadas rutas de bootstrap.

## Migración recomendada del repositorio

### 1. Declaración de dependencias

Mantén las dependencias normales de runtime en `[project].dependencies` y las funcionalidades opcionales orientadas al usuario en `[project.optional-dependencies]`:

- `google`: soporte de autenticación de Google.
- `tts`: runtime de Kokoro.
- `package`: herramientas de PyInstaller si siguen siendo un requisito de instalación.

Mueve las herramientas exclusivas de desarrollo a `[dependency-groups].dev` cuando se seleccione la configuración final de uv. Evita duplicar el mismo grafo de dependencias en `requirements*.txt`.

### 2. Locking y entornos locales

Versiona `uv.lock` y convierte `.venv` en el entorno canónico del proyecto. Los comandos previstos son:

```bash
uv sync
uv sync --extra google
uv sync --extra tts
uv sync --extra package
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv build
```

Utiliza `uv lock --upgrade` únicamente como operación explícita de actualización de dependencias. La CI debe utilizar el lockfile versionado en lugar de resolver un grafo nuevo en cada ejecución.

### 3. Scripts de instalación

`setup_env.sh` y `setup_env.bat` deben dejar de crear un entorno independiente gestionado por pip y delegar en `uv sync`. Las opciones existentes deben corresponder a extras en lugar de archivos requirements separados.

Ejemplos:

```text
instalación base       -> uv sync
soporte Google         -> uv sync --extra google
soporte TTS            -> uv sync --extra tts
herramientas packaging -> uv sync --extra package
```

Los scripts deben comprobar que uv existe y emitir un único mensaje claro de instalación cuando no esté disponible. No deben instalar uv implícitamente durante la ejecución normal de la aplicación.

### 4. run_local y schedulers

`run_local.sh` / `run_local.bat` deben seguir siendo dispatchers ligeros. Deben invocar el proyecto mediante `uv run` solo cuando se ejecuten desde un checkout del código fuente, conservando todos los argumentos y subcomandos existentes.

Los schedulers deben utilizar el mismo comando canónico del proyecto en lugar de instalar dependencias por sí mismos. Una entrada de scheduler debería ser conceptualmente:

```text
uv run video-translation-pipeline --scheduled ...
```

El diseño de producción debe evitar `uv sync` en cada ejecución programada. La sincronización pertenece al despliegue/bootstrap; la ejecución debe utilizar un entorno ya preparado.

### 5. Construcción y creación de ejecutables

Los scripts de build deben sustituir `python -m pip install -r requirements-dev.txt` por un único entorno sincronizado e invocar PyInstaller a través de ese entorno, por ejemplo:

```text
uv sync --extra package
uv run pyinstaller ...
```

Esto mantiene la construcción del ejecutable vinculada al mismo lockfile que las pruebas y el desarrollo local.

### 6. Instaladores de TTS y CUDA

**No** realices una sustitución mecánica de `pip -> uv` en todas partes.

`setup_tts.py` debería dejar de instalar finalmente las dependencias de Python por sí mismo. El script de bootstrap debería sincronizar las dependencias `tts`, mientras que el script Python debería limitarse a descargar/validar los recursos del modelo TTS.

`src/cuda_runtime.py` es un caso independiente de alto riesgo porque instala dinámicamente wheels de runtime NVIDIA en un directorio de runtime gestionado. Debe mantenerse sin cambios en la primera migración a uv salvo que un diseño específico demuestre que uv puede conservar su semántica de runtime aislado y su comportamiento multiplataforma.

### 7. Adaptación de CI

La CI final debe utilizar uv para:

- preparación del entorno;
- sincronización de dependencias;
- ejecución de pruebas;
- ejecución de Ruff;
- comprobaciones de compilación;
- construcción de paquetes;
- consistencia de resolución de dependencias.

La CI debe conservar pip para una prueba de compatibilidad deliberadamente aislada: instalar la wheel construida en un entorno nuevo mediante pip y ejecutar `pip check` junto con los puntos de entrada de consola publicados. Esto demuestra que uv no ha convertido accidentalmente el paquete distribuible en específico de uv.

La política existente de `pip-audit` puede mantenerse independientemente de la migración del instalador del proyecto.

### 8. Archivos requirements

Después de una auditoría de todo el repositorio que confirme que no existen consumidores externos, elimina los archivos de dependencias Python duplicados:

- `requirements.txt`
- `requirements-dev.txt`
- `requirements-google.txt`

`requirements-rclone.txt` no debe convertirse en una dependencia de uv porque rclone es un ejecutable externo, no un paquete Python. Puede mantenerse como archivo de bootstrap/documentación de herramientas externas o sustituirse por el bootstrap gestionado del proyecto (`uv run python main.py provider bootstrap`) y una documentación de instalación explícita.

## Criterios de aceptación de la migración

La migración completa no debe considerarse terminada hasta que se cumpla todo lo siguiente:

- `uv.lock` está versionado y es reproducible.
- La CI utiliza `uv sync --locked` y `uv run` para las operaciones del proyecto.
- Linux, Windows y macOS siguen cubiertos para Python 3.11, 3.12 y 3.13.
- Se ejercitan los extras Google, TTS y packaging.
- Los scripts `run_local`, scheduler y build ya no dependen de archivos requirements duplicados.
- Las construcciones PyInstaller siguen funcionando en sus plataformas compatibles.
- El comportamiento del runtime CUDA se valida explícitamente en lugar de reescribirse mecánicamente.
- La prueba de wheel limpia sigue funcionando mediante pip.
- La documentación ya no presenta los archivos requirements como vía principal de instalación.
- Una búsqueda en todo el repositorio no muestra instrucciones obsoletas accidentales `pip install -r requirements*.txt`.

Esta vista previa histórica registra deliberadamente el estado anterior a esos cambios de producción. La PR #42 completó la migración de infraestructura; `docs/UV_MIGRATION.md` es la referencia operativa actual.
