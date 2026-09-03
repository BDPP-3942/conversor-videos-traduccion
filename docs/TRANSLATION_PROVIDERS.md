# Proveedores de traducción

La configuración predeterminada del proyecto es:

```text
Mistral → Local CTranslate2 → DeepL → MyMemory
```

El provider local es autocontenido para el caso `es→en`: no requiere API, Ollama ni LM Studio una vez preparado el modelo. Los proveedores remotos continúan disponibles como alternativas configurables.

## Proveedor local

Modelo seleccionado y fijado:

```text
Repository: Prukario/opus-mt-es-en-ct2-int8
Revision: ad91ad1697ea1761111ff4c179400796d085b347
Runtime: CTranslate2 4.8.x + SentencePiece
Quantization: INT8
Idiomas: es → en
Tamaño aproximado: 82.5 MB
Licencia publicada del modelo: CC-BY-4.0
```

La conversión publicada es de Helsinki-NLP `opus-mt-es-en`; el modelo base oficial figura bajo Apache-2.0, mientras que la conversión distribuida seleccionada declara CC-BY-4.0. La distribución del modelo convertido debe conservar la atribución correspondiente.

Los ficheros principales `model.bin`, `source.spm` y `target.spm` se validan mediante tamaño y SHA-256 antes de cargarse. También se exige la presencia de los metadatos de CTranslate2 necesarios. Los recursos se guardan bajo:

```text
tools/models/translation/opus-mt-es-en-ct2-int8/
```

Preparación:

```bash
python scripts/manage_local_translation.py status
python scripts/manage_local_translation.py download
```

La descarga se realiza únicamente desde HTTPS en el repositorio/revisión fijados. Se descarga a un directorio temporal y se reemplaza atómicamente el modelo anterior solo después de completar la descarga. Las descargas parciales se conservan en `.part` para permitir reanudación cuando el servidor soporte Range.

## Configuración

```env
TRANSLATION_PROVIDER=mistral
TRANSLATION_FALLBACK_PROVIDERS=local,deepl,mymemory
LOCAL_TRANSLATION_MODEL_DIR=tools/models/translation/opus-mt-es-en-ct2-int8
LOCAL_TRANSLATION_DEVICE=auto
LOCAL_TRANSLATION_COMPUTE_TYPE=auto
LOCAL_TRANSLATION_BEAM_SIZE=2
LOCAL_TRANSLATION_AUTO_DOWNLOAD=false
```

`LOCAL_TRANSLATION_AUTO_DOWNLOAD=false` es intencionado: la ejecución normal no inicia una descarga costosa sin consentimiento. En una sesión interactiva puede habilitarse y el provider pedirá confirmación mostrando recurso, revisión, tamaño, destino, motivo y licencia. Para preparación explícita se recomienda el script de gestión.

## Ollama y LM Studio

Ollama y LM Studio no son requisitos ni forman parte del provider local incorporado. Pueden añadirse como providers HTTP independientes en el futuro, pero su ausencia no impide utilizar la traducción local autocontenida.

## Fallback

El orden de fallback se configura mediante `TRANSLATION_FALLBACK_PROVIDERS`. El orquestador mantiene el mapping por índice de segmento: un provider puede traducir solo los segmentos que permanecen sin resolver y el resultado se vuelve a asociar al cue original. Los errores de cuota, rate limit, timeout y servicio temporal se registran de forma diferenciada; los errores permanentes también pueden provocar el siguiente provider cuando el contrato del orquestador los clasifica como recuperables.

## Providers remotos

Las credenciales son específicas por proveedor: Mistral necesita `MISTRAL_API_KEY`, DeepL necesita `DEEPL_API_KEY` y MyMemory puede funcionar sin clave. Google y Microsoft siguen disponibles mediante su configuración existente.

## Batching y concurrencia

El pipeline traduce en lotes y reutiliza la instancia del provider durante la ejecución. El mapping por índice evita depender del orden de finalización de requests concurrentes. Los límites conservadores por proveedor continúan aplicándose a los servicios remotos; el provider local no necesita rate limiting de red.

## Privacidad

El provider local procesa los textos dentro de la máquina. Los providers remotos solo reciben el texto necesario para traducir; timestamps y estructura VTT se conservan localmente.
