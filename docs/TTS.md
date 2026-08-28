# TTS sincronizado

La generación TTS es opcional y está desactivada por defecto. Cuando `TTS_ENABLED=true`, el flujo común de almacenamiento ejecuta el TTS después de disponer de un vídeo normal y un VTT traducido válido. Antes de sintetizar se comprueban y, cuando es posible, se reparan los VTT.

## Flujo

```text
Vídeo / ZIP
   ↓
Whisper + timestamps de palabra
   ↓
segmentación de pausas largas
   ↓
VTT original validado
   ↓
traducción conservando timestamps
   ↓
VTT traducido validado
   ↓
reparación si un VTT existente no es válido
   ↓
TTS por cue
   ↓
WAV con silencios entre cues
   ↓
MP4 TTS + WebM TTS opcional
```

El VTT original es la fuente de verdad temporal. La traducción no debe modificar `start` ni `end`. TTS rechaza cualquier cue con `start < 0`, `end <= start`, timestamps desordenados o sintaxis WebVTT inválida.

## Recuperación de VTT

Los resultados históricos pueden contener cues inválidos, especialmente `start >= end`. Un VTT inválido no se utiliza para reproducción ni para TTS.

La recuperación contempla tres casos:

1. **Original/STT inválido o ausente:** se reutiliza el vídeo normal existente, se ejecuta STT y después se traduce.
2. **Original válido y traducción inválida o ausente:** se reutilizan los timestamps originales y solo se vuelve a traducir.
3. **Ambos inválidos:** se ejecuta STT una vez y, tras validarlo, se reconstruye la traducción.

Los artefactos sustituidos se respaldan antes de aplicar el nuevo VTT. El vídeo normal no se regenera durante esta recuperación.

Consulta [`VTT_REPAIR.md`](VTT_REPAIR.md).

## Proveedor local

La implementación inicial utiliza Kokoro mediante `kokoro-onnx`.

La instalación recomendada es:

```bash
./scripts/setup_env.sh --tts
```

en macOS/Linux, o:

```bat
scripts\setup_env.bat --tts
```

o bien ejecutar los instaladores normales con `TTS_ENABLED=true` en `.env`. En ese caso el instalador detecta la configuración, instala el extra `[tts]`, crea `tools/tts/` y descarga automáticamente los dos artefactos Kokoro de la release oficial de `kokoro-onnx`.

Los pesos no están incluidos en Git y se guardan por defecto en:

```text
tools/tts/kokoro-v1.0.onnx
tools/tts/voices-v1.0.bin
```

También se pueden especificar rutas externas mediante `TTS_MODEL_PATH` y `TTS_VOICES_PATH`.

## Configuración

Los parámetros relevantes pueden establecerse en `config/app.toml` o mediante las variables `TTS_*` para ejecución desatendida:

```dotenv
TTS_ENABLED=true
TTS_REQUIRED=false
TTS_PROVIDER=kokoro
TTS_VOICE=af_sarah
TTS_MODEL_PATH=tools/tts/kokoro-v1.0.onnx
TTS_VOICES_PATH=tools/tts/voices-v1.0.bin
TTS_SPEED=1.0
TTS_MAX_SPEED=1.35
TTS_DURATION_TOLERANCE=0.02
TTS_SAMPLE_RATE=24000
TTS_AUDIO_BITRATE=192k
TTS_WEBM_AUDIO_BITRATE=192k
TTS_GENERATE_WEBM=true
```

`TTS_ENABLED=true` activa el postprocesado desde el pipeline común. El instalador prepara automáticamente la dependencia y los pesos cuando utiliza las rutas predeterminadas.

El comando `python main.py doctor` valida que, si TTS está habilitado, existan tanto `kokoro-onnx` como el modelo y el fichero de voces antes de iniciar el procesamiento.

## Sincronización

Cada cue se sintetiza dentro de su intervalo temporal. Si la duración inicial no cabe, el generador intenta aumentar la velocidad hasta `max_speed`. Si sigue sin caber dentro de la tolerancia configurada, el cue falla en lugar de solaparse con el siguiente.

Los huecos entre cues permanecen como silencio. No se genera un único audio continuo que ignore los timestamps.

## Artefactos

```text
<stem>_tts.wav
<stem>_tts.mp4
<stem>_tts.webm
```

El MP4 conserva el vídeo normal y sustituye/añade la pista de audio TTS. Para WebM se utiliza el WebM normal cuando está disponible; si no, se genera un WebM compatible según la configuración.

## Primera ejecución y resultados existentes

En una primera ejecución, el TTS se procesa después de la creación del vídeo normal y del VTT traducido.

En resultados ya procesados, no es necesario volver a colocar los vídeos originales en `storage/input` si el vídeo normal sigue disponible en la carpeta de salida. La reparación puede regenerar STT sobre ese vídeo cuando el VTT original no sea fiable.

Un TTS ya existente se reutiliza si los subtítulos siguen siendo válidos. Si la reparación cambia el VTT, el TTS se vuelve a generar para mantener la correspondencia temporal y textual.

## Cloud y rclone

No existe un pipeline TTS independiente por proveedor. El mismo decorador de almacenamiento funciona con local, Google Drive y rclone: descarga temporalmente los artefactos necesarios, ejecuta la síntesis y sube los resultados al mismo destino.

Un fallo de TTS no elimina el vídeo normal ni los VTT válidos.

## Ejecución programada y ejecutable

`run_local`, `main.py run --scheduled`, Task Scheduler, launchd, cron y el ejecutable deben utilizar el mismo directorio de trabajo, configuración, credenciales y pesos. No se requiere interacción durante TTS.

## Licencias

La licencia de `kokoro-onnx` o de cualquier otra librería no determina por sí sola las condiciones de los modelos, voces, datos de fonemización o dependencias transitivas. Antes de redistribuir un ejecutable o utilizar el resultado comercialmente debe revisarse la cadena completa de licencias.

## Limitaciones

- Los pesos no se incluyen en Git.
- La generación local requiere instalar `[tts]` y disponer de los pesos configurados.
- La calidad depende del idioma y la voz disponibles.
- Un fallo TTS puede dejar el resultado tradicional válido pero impedir que el trabajo se marque como completo cuando `TTS_REQUIRED=true`.
