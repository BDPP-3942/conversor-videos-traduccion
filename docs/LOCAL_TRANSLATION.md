# Local translation runtime

El proveedor local usa CTranslate2 + SentencePiece y está pensado como fallback offline cuando un proveedor remoto como Mistral está limitado o no disponible.

## Modelo fijado

```text
Model: cstr/madlad400-3b-ct2-int8
Revision: 12eff26f7d93623e2b2d3b5345e5863e14599dae
Task: Spanish → English
Quantization: INT8
Model weights: ~2.95 GB
Installation budget: < 3 GB
License: Apache-2.0
```

MADLAD-400 3B es un modelo multilingüe de traducción de mayor capacidad que el OPUS-MT anterior. La conversión CTranslate2 INT8 se mantiene dentro del límite de almacenamiento del proyecto y puede ejecutarse en CPU; CUDA sigue siendo opcional cuando existe un runtime compatible.

La revisión está fijada. `model.bin` y `sentencepiece.model` se validan por tamaño y SHA-256; `config.json` y `shared_vocabulary.json` se validan como JSON. También se comprueba el tamaño total instalado para evitar superar 3 GB.

## Espacio necesario

El modelo final ocupa aproximadamente 2.95 GB. La preparación usa temporalmente la caché de Hugging Face antes de mover los ficheros a su destino, por lo que se recomienda disponer de **al menos ~6 GB libres** durante la instalación, además del espacio que se quiera conservar para otros recursos del programa.

Si el modelo ya está preparado, la ejecución offline solo necesita el directorio gestionado del modelo.

## Preparación

```bash
python scripts/manage_local_translation.py status
python scripts/manage_local_translation.py download
python scripts/benchmark_local_translation.py --sentences 1
```

La descarga usa `huggingface_hub.hf_hub_download` con el repositorio y revisión fijados. Los repositorios públicos normalmente no necesitan autenticación. Si el entorno de Hugging Face exige autenticación, puede proporcionarse `LOCAL_TRANSLATION_HF_TOKEN` o `HF_TOKEN`; el token solo se utiliza durante la descarga y no se almacena con el modelo.

La descarga se realiza sobre un directorio temporal gestionado y solo sustituye el modelo final después de superar las validaciones de integridad.

Para eliminar el modelo:

```bash
python scripts/manage_runtime_resources.py translation-model cleanup
```

La limpieza solo afecta al modelo gestionado bajo `tools/models/translation/madlad400-3b-ct2-int8/`.

## Configuración

```env
TRANSLATION_PROVIDER=local
TRANSLATION_FALLBACK_PROVIDERS=deepl,mymemory
LOCAL_TRANSLATION_MODEL_DIR=tools/models/translation/madlad400-3b-ct2-int8
LOCAL_TRANSLATION_MODEL_ID=cstr/madlad400-3b-ct2-int8
LOCAL_TRANSLATION_MODEL_REVISION=12eff26f7d93623e2b2d3b5345e5863e14599dae
LOCAL_TRANSLATION_DEVICE=auto
LOCAL_TRANSLATION_COMPUTE_TYPE=auto
LOCAL_TRANSLATION_BEAM_SIZE=2
LOCAL_TRANSLATION_AUTO_DOWNLOAD=false
LOCAL_TRANSLATION_HF_TOKEN=
```

`LOCAL_TRANSLATION_MODEL_ID` y `LOCAL_TRANSLATION_MODEL_REVISION` solo aceptan el modelo y la revisión fijados por el proyecto; no sirven para seleccionar arbitrariamente otro modelo.

El modelo actual se usa para es→en. La cadena general puede utilizar `Mistral → local → DeepL → MyMemory`.

## CPU/GPU

`auto` selecciona CUDA solo después de validar el runtime NVIDIA/CTranslate2. Si no existe una GPU NVIDIA utilizable, el proveedor local usa CPU `int8`. Si la comprobación real de CTranslate2 CUDA falla, vuelve a CPU `int8` de forma conservadora.

En macOS, la ruta esperada es CPU `int8`. El rendimiento debe medirse en el Mac concreto; el objetivo de este cambio es priorizar calidad y ejecución local dentro del límite de almacenamiento, no prometer una velocidad determinada.

## Batching

El proveedor mantiene una instancia del modelo y traduce lotes preservando el orden. Timestamps e IDs VTT se mantienen fuera del modelo.

## Benchmark y prueba funcional

```bash
python scripts/benchmark_local_translation.py --sentences 100
```

El benchmark inicializa CTranslate2 + SentencePiece y comprueba que cada entrada produzca una salida textual no vacía. Para una instalación real en macOS, se recomienda ejecutar como mínimo `status` y un benchmark de una frase antes de procesar vídeos completos.

## Privacidad/offline

Una vez preparado el modelo, la traducción local no requiere API externa ni conexión a Internet. La autenticación de Hugging Face, si se configura, solo afecta a la preparación/descarga y no a la ejecución offline posterior.

## Attribution

MADLAD-400 declara licencia Apache-2.0. La conversión utilizada es `cstr/madlad400-3b-ct2-int8` y se mantiene fijada a la revisión indicada arriba.
