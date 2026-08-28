# TTS sincronizado

La generación TTS es opcional y está desactivada por defecto. Cuando `TTS_ENABLED=true`, `python main.py run` ejecuta una fase común de postprocesado sobre las carpetas de salida. Esa fase valida/repara los VTT y genera los artefactos TTS usando exactamente el mismo almacenamiento local, Google Drive o rclone seleccionado por el pipeline.

## Flujo

```text
Vídeo / ZIP
  ↓
Whisper + timestamps de palabra
  ↓
separación de pausas largas
  ↓
VTT original validado
  ↓
traducción conservando timestamps
  ↓
VTT traducido validado
  ↓
postprocesado TTS
  ↓
TTS por cue
  ↓
audio colocado en su timestamp
  ↓
WAV completo con silencios
  ↓
MP4 TTS + WebM TTS opcional
```

Whisper utiliza `word_timestamps=true` para detectar pausas internas. El umbral se configura con `whisper_min_silence_duration_ms` o `WHISPER_MIN_SILENCE_DURATION_MS`.

## Recuperación de VTT

TTS nunca debe ejecutarse con un VTT inválido. Antes de sintetizar se comprueba que cada cue tenga `start >= 0`, `end > start`, orden temporal correcto y sintaxis WebVTT válida.

Si existe un vídeo normal y el VTT original es inválido, el sistema regenera STT desde ese vídeo. Si la traducción es inválida, se vuelve a traducir a partir de la transcripción válida. Si ambos VTT son inválidos, se ejecutan ambas recuperaciones en ese orden. Los vídeos normales ya procesados no se vuelven a convertir.

Consulta [`docs/VTT_RECOVERY.md`](VTT_RECOVERY.md).

## Proveedor local

La implementación inicial usa **Kokoro mediante `kokoro-onnx`**. El paquete se carga de forma diferida.

Instalación:

```bash
python -m pip install -e ".[tts]"
```

Deben existir los pesos configurados:

```text
tools/tts/kokoro-v1.0.onnx
tools/tts/voices-v1.0.bin
```

## Configuración

En `config/app.toml`:

```toml
[tts]
enabled = true
required = false
provider = "kokoro"
voice = "af_sarah"
model_path = "tools/tts/kokoro-v1.0.onnx"
voices_path = "tools/tts/voices-v1.0.bin"
speed = 1.0
max_speed = 1.35
duration_tolerance = 0.02
sample_rate = 24000
audio_bitrate = "192k"
webm_audio_bitrate = "192k"
generate_webm = true
```

Los equivalentes `TTS_*` pueden utilizarse para despliegues desatendidos. `TTS_ENABLED=true` activa la fase desde `main.py run`; no descarga modelos.

## Sincronización

Si un cue ocupa `10.000 → 14.500`, su audio se coloca dentro de ese intervalo. Cuando el audio no cabe se intenta aumentar la velocidad hasta `max_speed`. Si sigue sin caber dentro de la tolerancia configurada, el cue falla en lugar de solaparse con el siguiente.

Los huecos entre cues permanecen en silencio. Los cues vacíos no generan audio. Los timestamps inválidos se rechazan antes de sintetizar.

## Artefactos

```text
<stem>_tts.wav
<stem>_tts.mp4
<stem>_tts.webm
```

El MP4 conserva el vídeo normal y mezcla el audio TTS como AAC. Si existe un WebM normal se utiliza como fuente para el WebM TTS; en caso contrario se genera un WebM compatible.

## Primera ejecución y resultados existentes

En una primera ejecución, después de crear el vídeo normal, STT y traducción, `run` ejecuta el postprocesado TTS si está habilitado.

En resultados ya procesados, `run` inspecciona las carpetas existentes. Puede reparar VTT y generar TTS sin volver a insertar los vídeos en `storage/input`, siempre que el vídeo normal siga disponible en la carpeta de salida.

Un `_tts.mp4` existente se reutiliza si los subtítulos no han tenido que repararse. Si se repara STT o traducción, el TTS se vuelve a generar para que el audio corresponda al nuevo timing/texto.

## Cloud y rclone

No existe un pipeline TTS distinto por proveedor. El postprocesador descarga temporalmente vídeo/VTT desde el backend, ejecuta el mismo generador y vuelve a subir los artefactos. La fuente no se elimina desde TTS.

## Ejecución programada y ejecutable

`run_local`, `main.py run --scheduled`, Task Scheduler, launchd, cron y el ejecutable deben utilizar el mismo directorio de trabajo, configuración, credenciales y pesos. No se requiere interacción durante TTS.

## Licencias

La cadena debe revisarse completa antes de redistribuir un ejecutable comercial. La licencia de una librería no implica automáticamente que todos los modelos, voces, datos de fonemización y dependencias transitivas tengan las mismas condiciones.

## Limitaciones

- Los pesos no se incluyen en Git.
- La generación local requiere instalar `[tts]` y proporcionar ambos pesos.
- La calidad depende del idioma y voz seleccionados.
- Un fallo TTS no debe ocultar un fallo de STT/traducción; el resultado se informa como parcial o error según la configuración y el punto de fallo.
