# Local translation runtime

PR2 añade un proveedor opcional de traducción local basado en CTranslate2 + SentencePiece.

## Modelo actual

```text
Model: Prukario/opus-mt-es-en-ct2-int8
Revision: ad91ad1697ea1761111ff4c179400796d085b347
Task: Spanish → English
Quantization: INT8
Approximate download: 82.5 MiB
License: CC-BY-4.0
```

La revisión está fijada. `model.bin`, `source.spm` y `target.spm` se validan por tamaño y SHA-256; los tres metadatos JSON obligatorios también se validan por presencia, tipo JSON y estructura mínima antes de considerar utilizable el modelo.

## Preparación

```bash
python scripts/manage_local_translation.py status
python scripts/manage_local_translation.py download
```

Para eliminar el modelo:

```bash
python scripts/manage_runtime_resources.py translation-model cleanup
```

La limpieza solo afecta al modelo gestionado bajo `tools/models/translation/opus-mt-es-en-ct2-int8/`.

## Configuración

La configuración específica del proveedor local se expone actualmente mediante variables de entorno. No existen campos `[local_translation]` en `config/app.toml`; añadir una variable al `.env` o al entorno de ejecución es la forma soportada de personalizar el proveedor local.

```env
TRANSLATION_PROVIDER=local
TRANSLATION_FALLBACK_PROVIDERS=deepl,mymemory
LOCAL_TRANSLATION_MODEL_DIR=tools/models/translation/opus-mt-es-en-ct2-int8
LOCAL_TRANSLATION_MODEL_ID=Prukario/opus-mt-es-en-ct2-int8
LOCAL_TRANSLATION_MODEL_REVISION=ad91ad1697ea1761111ff4c179400796d085b347
LOCAL_TRANSLATION_DEVICE=auto
LOCAL_TRANSLATION_COMPUTE_TYPE=auto
LOCAL_TRANSLATION_BEAM_SIZE=2
LOCAL_TRANSLATION_AUTO_DOWNLOAD=false
```

Estas variables se aplican como overrides de entorno, igual que el resto de variables documentadas en `.env.example`. `LOCAL_TRANSLATION_MODEL_ID` y `LOCAL_TRANSLATION_MODEL_REVISION` solo aceptan el modelo y la revisión fijados por el proyecto; no sirven para seleccionar arbitrariamente otro modelo.

El modelo actual soporta es→en. La cadena general puede utilizar `Mistral → local → DeepL → MyMemory`. Un recurso local ausente/corrupto se trata como fallo de recurso y puede permitir fallback; una configuración inválida no se convierte silenciosamente en otro proveedor.

## CPU/GPU

`auto` selecciona CUDA solo después de validar el runtime NVIDIA/CTranslate2. Si no existe una GPU NVIDIA utilizable, el proveedor local usa CPU `int8`. Si se solicita CUDA y la comprobación real de CTranslate2 falla, el proveedor vuelve a CPU `int8` de forma conservadora.

Consulta [`CUDA.md`](CUDA.md) para el diagnóstico e instalación gestionada de las bibliotecas necesarias para Whisper/CTranslate2.

## Batching

El proveedor mantiene una instancia del modelo y traduce lotes preservando el orden. El pipeline vuelve a asociar cada resultado con su cue original; timestamps e IDs VTT se mantienen fuera del modelo.

## Benchmark

```bash
python scripts/benchmark_local_translation.py --sentences 100
```

El benchmark informa revisión, hardware, RAM, dispositivo, compute type, cues, caracteres, carga, tiempo de traducción, throughput y tiempo por cue. No se considera verificado ningún benchmark hasta ejecutarlo en el hardware correspondiente.

## Privacidad/offline

Una vez preparado el modelo, la traducción local no requiere API externa ni conexión a Internet. La preparación descarga únicamente desde el origen y revisión fijados.

## Attribution

La conversión seleccionada declara CC-BY-4.0 y tiene como base `Helsinki-NLP/opus-mt-es-en`. Consulte `THIRD_PARTY_NOTICES.md` para las obligaciones de distribución.
