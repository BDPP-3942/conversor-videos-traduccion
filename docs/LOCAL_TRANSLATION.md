# Local translation runtime

El proveedor local usa CTranslate2 + SentencePiece y está pensado como fallback offline cuando un proveedor remoto como Mistral está limitado o no disponible. **El proyecto conserva dos modelos locales fijados**: MADLAD-400 3B como opción de mayor calidad y OPUS-MT como opción ligera de compatibilidad cuando el espacio o el rendimiento de CPU sean prioritarios.

## Modelos fijados

### MADLAD-400 3B — opción predeterminada

```text
Model: cstr/madlad400-3b-ct2-int8
Revision: 12eff26f7d93623e2b2d3b5345e5863e14599dae
Task: Spanish → English
Quantization: INT8
Model weights: ~2.95 GB
Installation budget: < 3 GB
License: Apache-2.0
```

La revisión está fijada. `model.bin` y `sentencepiece.model` se validan por tamaño y SHA-256; `config.json` y `shared_vocabulary.json` se validan como JSON. También se comprueba el tamaño total instalado para evitar superar 3 GB.

### OPUS-MT — opción ligera conservada

```text
Model: Prukario/opus-mt-es-en-ct2-int8
Revision: ad91ad1697ea1761111ff4c179400796d085b347
Task: Spanish → English
Quantization: INT8
Approximate download: 82.5 MB (~78.7 MiB)
License: CC-BY-4.0
```

Esta opción **no ha sido eliminada** por la incorporación de MADLAD. `model.bin`, `source.spm` y `target.spm` se validan por tamaño y SHA-256, y sus metadatos JSON obligatorios también se validan. Conserva además los metadatos empaquetados `config.json` y `tokenizer_config.json` que necesita su preparación.

## Selección

MADLAD es el valor predeterminado. Para seleccionar OPUS-MT hay que cambiar conjuntamente el modelo, directorio, repositorio y revisión; no se debe mezclar la revisión de un modelo con los ficheros del otro:

```env
LOCAL_TRANSLATION_MODEL=opus-mt-es-en-ct2-int8
LOCAL_TRANSLATION_MODEL_DIR=tools/models/translation/opus-mt-es-en-ct2-int8
LOCAL_TRANSLATION_MODEL_ID=Prukario/opus-mt-es-en-ct2-int8
LOCAL_TRANSLATION_MODEL_REVISION=ad91ad1697ea1761111ff4c179400796d085b347
```

Para volver a MADLAD:

```env
LOCAL_TRANSLATION_MODEL=madlad400-3b-ct2-int8
LOCAL_TRANSLATION_MODEL_DIR=tools/models/translation/madlad400-3b-ct2-int8
LOCAL_TRANSLATION_MODEL_ID=cstr/madlad400-3b-ct2-int8
LOCAL_TRANSLATION_MODEL_REVISION=12eff26f7d93623e2b2d3b5345e5863e14599dae
```

La configuración por entorno sigue siendo deliberada: el modelo local no se descarga ni se activa automáticamente por defecto.

## Espacio necesario

MADLAD ocupa aproximadamente 2.95 GB. Su preparación puede requerir temporalmente unos **6 GB libres**. OPUS-MT requiere mucho menos espacio y conserva su utilidad en máquinas con almacenamiento limitado.

## Preparación

```bash
python scripts/manage_local_translation.py status
python scripts/manage_local_translation.py download
python scripts/benchmark_local_translation.py --sentences 1
```

El gestor valida el repositorio y la revisión fijados antes de descargar. La descarga utiliza `huggingface_hub.hf_hub_download`; los repositorios públicos normalmente no necesitan autenticación. Si el entorno de Hugging Face exige autenticación, puede proporcionarse `LOCAL_TRANSLATION_HF_TOKEN` o `HF_TOKEN`; el token solo se utiliza durante la descarga y no se almacena con el modelo.

La descarga se realiza sobre un directorio temporal gestionado y solo sustituye el modelo final después de superar las validaciones de integridad.

Para eliminar el modelo actualmente seleccionado:

```bash
python scripts/manage_runtime_resources.py translation-model cleanup
```

## Configuración completa

```env
TRANSLATION_PROVIDER=local
TRANSLATION_FALLBACK_PROVIDERS=deepl,mymemory
LOCAL_TRANSLATION_MODEL=madlad400-3b-ct2-int8
LOCAL_TRANSLATION_MODEL_DIR=tools/models/translation/madlad400-3b-ct2-int8
LOCAL_TRANSLATION_MODEL_ID=cstr/madlad400-3b-ct2-int8
LOCAL_TRANSLATION_MODEL_REVISION=12eff26f7d93623e2b2d3b5345e5863e14599dae
LOCAL_TRANSLATION_DEVICE=auto
LOCAL_TRANSLATION_COMPUTE_TYPE=auto
LOCAL_TRANSLATION_BEAM_SIZE=2
LOCAL_TRANSLATION_AUTO_DOWNLOAD=false
LOCAL_TRANSLATION_HF_TOKEN=
```

La cadena general puede utilizar `Mistral → local → DeepL → MyMemory`. Un recurso local ausente/corrupto se trata como fallo de recurso y puede permitir fallback; una configuración inválida no se convierte silenciosamente en otro proveedor.

## CPU/GPU

`auto` selecciona CUDA solo después de validar el runtime NVIDIA/CTranslate2. Si no existe una GPU NVIDIA utilizable, el proveedor local usa CPU `int8`. Si la comprobación real de CTranslate2 CUDA falla, vuelve a CPU `int8` de forma conservadora.

En macOS, la ruta esperada es CPU `int8`. MADLAD está orientado a calidad pero consume mucho más espacio; OPUS-MT sigue disponible como alternativa ligera. El rendimiento debe medirse en el Mac concreto.

## Batching y tokenización

MADLAD utiliza su `sentencepiece.model` compartido y el prefijo de destino `<2en>`. OPUS-MT conserva sus tokenizadores `source.spm` y `target.spm`. Ambos mantienen el orden de los lotes; timestamps e IDs VTT se gestionan fuera del modelo.

## Benchmark y prueba funcional

```bash
python scripts/benchmark_local_translation.py --sentences 100
```

El benchmark inicializa CTranslate2 + SentencePiece y comprueba que cada entrada produzca una salida textual no vacía. Para una instalación real, se recomienda ejecutar `status` y un benchmark de una frase antes de procesar vídeos completos.

## Privacidad/offline

Una vez preparado el modelo, la traducción local no requiere API externa ni conexión a Internet. La autenticación de Hugging Face, si se configura, solo afecta a la preparación/descarga y no a la ejecución offline posterior.

## Attribution

MADLAD-400 declara Apache-2.0. La conversión es `cstr/madlad400-3b-ct2-int8`. OPUS-MT utiliza la conversión `Prukario/opus-mt-es-en-ct2-int8` bajo CC-BY-4.0. Ambas referencias permanecen fijadas y documentadas.