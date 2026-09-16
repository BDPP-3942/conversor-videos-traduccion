# Pruebas

La suite de pruebas se configura mediante `pyproject.toml` y se encuentra bajo `tests/`.

## Comprobaciones locales

```bash
uv lock --check
uv sync --locked --extra google --group dev
uv pip check
uv run pytest -q
uv run ruff check .
uv run ruff check . --select S
uv run ruff format --check .
uv run python -m compileall .
uv build
```

Para ejecutar una prueba concreta:

```bash
uv run pytest tests/test_pipeline.py
uv run pytest tests/test_tts_pipeline.py
uv run pytest tests/test_reprocessor.py
uv run pytest tests/test_file_naming.py
uv run pytest tests/test_naming_reference.py
uv run pytest tests/test_extractor.py
uv run pytest tests/test_local_translation.py
```

## Áreas cubiertas

El repositorio contiene pruebas para recuperación de la CLI, extracción, resolución de FFmpeg, nombres, almacenamiento local, identidad/conversión multimedia, renovación OAuth, deduplicación, límites de rutas, rendimiento/gestión de recursos, ejecución del pipeline, runtime de proveedores, resume, configuración, URI/estructura de almacenamiento, STT, QA/reparación de subtítulos, traducción, gestión de cuotas, TTS y disponibilidad desatendida.

Las pruebas de nombres cubren ambas capas del contrato: inferencia del nombre lógico de ZIP/curso/recurso y representación física final del sistema de archivos. La normalización física sigue NFD → eliminación de marcas diacríticas combinantes → NFC y después aplica minúsculas/case-fold a la representación física; entradas como `ñ` y `é` se convierten por tanto en `n` y `e`. Las pruebas también cubren normalización de separadores, gestión de puntuación/caracteres de control, nombres reservados de Windows, límites de componentes UTF-8 y el separador de ámbito `x`.

Las pruebas ZIP cubren traversal, rutas absolutas/UNC de Windows, componentes reservados de Windows, archivos comprimidos anidados, canonicalización NFC y colisiones Unicode mediante case-fold. Estas comprobaciones son fronteras de seguridad y deben ejecutarse en todas las plataformas compatibles.

Las pruebas de traducción local cubren la validación del modelo fijado, descargas reanudables, autorización opcional de Hugging Face, fallback a CPU cuando falla la detección de CUDA y el contrato de salida por lotes de CTranslate2/SentencePiece. La suite normal de pruebas unitarias utiliza mocks y no requiere descargar el modelo ni disponer de una GPU.

El benchmark de traducción local es la prueba smoke a nivel de hardware:

```bash
uv run python scripts/benchmark_local_translation.py --sentences 100
```

Debe ejecutarse en el equipo de destino después de preparar el modelo. Verifica la inicialización real del modelo y rechaza una salida de traducción vacía.

Los proveedores externos deben probarse con mocks deterministas en lugar de requerir acceso a red en vivo. Las descargas de modelos y la ejecución GPU son cuestiones de integración y no deben convertirse en requisitos de la suite normal de pruebas unitarias.

Los nombres de comandos, flags, dependencias, rutas y APIs se conservan literalmente en esta documentación para que los ejemplos sean ejecutables.
