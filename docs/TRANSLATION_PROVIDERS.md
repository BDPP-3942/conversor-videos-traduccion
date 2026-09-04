# Proveedores de traducción

La configuración predeterminada del proyecto es:

```text
Mistral → Local CTranslate2 → DeepL → MyMemory
```

Mistral sigue siendo el proveedor activo por defecto; el proveedor local es el primer fallback y permite continuar sin otro proveedor remoto cuando el modelo local ya está preparado. Si el recurso local no está disponible o no puede inicializarse por un fallo de recurso, la cadena continúa con DeepL y MyMemory según la configuración efectiva. Una configuración inválida del proveedor no se convierte silenciosamente en otro proveedor.

El objetivo es que una instalación personal pueda funcionar sin Google Cloud ni Azure. Las credenciales son opcionales por proveedor: Mistral necesita `MISTRAL_API_KEY`, DeepL necesita `DEEPL_API_KEY` y MyMemory puede funcionar sin clave.

## Configuración

```env
TRANSLATION_PROVIDER=mistral
TRANSLATION_FALLBACK_PROVIDERS=local,deepl,mymemory
MISTRAL_API_KEY=...
MISTRAL_MODEL=mistral-small-latest
DEEPL_API_KEY=...
MYMEMORY_EMAIL=...
```

El proveedor local se configura mediante `LOCAL_TRANSLATION_*`. Solo admite actualmente español→inglés y utiliza el modelo/revisión fijados por el proyecto; la preparación del modelo es explícita y está documentada en `LOCAL_TRANSLATION.md`.

```env
LOCAL_TRANSLATION_MODEL_DIR=tools/models/translation/opus-mt-es-en-ct2-int8
LOCAL_TRANSLATION_MODEL_ID=Prukario/opus-mt-es-en-ct2-int8
LOCAL_TRANSLATION_MODEL_REVISION=ad91ad1697ea1761111ff4c179400796d085b347
LOCAL_TRANSLATION_DEVICE=auto
LOCAL_TRANSLATION_COMPUTE_TYPE=auto
LOCAL_TRANSLATION_BEAM_SIZE=2
LOCAL_TRANSLATION_AUTO_DOWNLOAD=false
```

`MYMEMORY_EMAIL` es opcional. Si se proporciona, el cliente envía el parámetro `de` de MyMemory y el control local utiliza la cuota registrada conservadora; si no se proporciona, utiliza la cuota anónima conservadora.

## Límites locales

El proyecto no intenta adivinar límites que el proveedor pueda cambiar. Los límites de volumen que sí son suficientemente estables para proteger los planes gratuitos se controlan localmente:

| Proveedor | Control local | Valor conservador | Ventana |
|---|---|---:|---|
| Mistral | rate/concurrency | 2 requests concurrentes | continuo |
| DeepL | caracteres | 500.000 caracteres | mes |
| DeepL | rate/concurrency | 2 requests concurrentes | continuo |
| MyMemory anónimo | requests | 100 requests | día |
| MyMemory con email | requests | 1.000 requests | día |
| MyMemory | rate/concurrency | 1 request concurrente | continuo |

Los valores de concurrencia son **límites de seguridad del cliente**, no una afirmación de que el proveedor garantice exactamente ese número de requests paralelas. Se pueden reducir si una cuenta recibe 429.

## Batching

El pipeline traduce en lotes para reducir el número de requests:

- Mistral: hasta 25 segmentos por request por defecto.
- DeepL: hasta 25 segmentos por request por defecto.
- MyMemory: 1 segmento por request.
- Local CTranslate2: batching local sin request de red; el orden de los cues se conserva fuera del modelo.

El parámetro global es:

```env
TRANSLATION_BATCH_SIZE=25
```

El cliente nunca permite que esta opción supere su límite seguro específico de proveedor.

## Concurrencia

Hay dos controles:

```env
TRANSLATION_MAX_PARALLEL_REQUESTS=2
TRANSLATION_PROVIDER_MAX_PARALLEL_REQUESTS=0
```

El primero limita la concurrencia global de traducción. El segundo, cuando es mayor que `0`, sustituye el límite conservador por proveedor.

Por defecto para proveedores remotos:

```text
Mistral   2
DeepL     2
MyMemory  1
```

La traducción local no realiza requests de red y no utiliza estos límites HTTP; su paralelismo está sujeto al presupuesto de recursos del proceso/pipeline y al runtime CTranslate2.

No se recomienda aumentar `TRANSLATION_PROVIDER_MAX_PARALLEL_REQUESTS` en una cuenta gratuita sin comprobar primero los límites actuales del proveedor.

## Rate limiting y retry

Cada proveedor remoto mantiene su propio reloj de intervalo mínimo. Los errores `429` se distinguen de errores de cuota/autorización. Los reintentos utilizan backoff exponencial con jitter y, si el proveedor sigue sin estar disponible, el lote pasa al siguiente proveedor.

El proveedor local no aplica rate limiting HTTP ni reintentos de red; los fallos de recurso/runtime se clasifican para que la cadena de fallback pueda continuar cuando corresponda.

La configuración predeterminada es:

```env
TRANSLATION_RETRIES=3
TRANSLATION_MAX_RETRIES_PER_PROVIDER=3
TRANSLATION_RETRY_DELAY_SECONDS=1.5
TRANSLATION_MIN_REQUEST_INTERVAL_SECONDS=0.5
TRANSLATION_MAX_BACKOFF_SECONDS=16
```

## Persistencia de cuota

El consumo reservado se guarda en:

```text
storage/state/translation_quotas.json
```

Esto evita que una segunda ejecución del proceso ignore el consumo realizado por una ejecución anterior. Las reservas se hacen antes de enviar una request y se mantienen de forma conservadora si esa request termina fallando.

La traducción local no consume esta cuota porque no realiza requests HTTP.

## Privacidad

El proyecto no envía timestamps ni estructura VTT al proveedor como datos de control. En proveedores remotos se envía únicamente el texto de los segmentos necesario para traducirlo y la respuesta se vuelve a asociar a los segmentos originales. La traducción local procesa el texto en el propio equipo una vez preparado el modelo. Los timestamps `start`/`end` se conservan localmente.

La política de privacidad concreta de cada proveedor remoto debe comprobarse antes de utilizarlo con contenido sensible; este documento describe el comportamiento técnico del cliente y no sustituye los términos del proveedor.
