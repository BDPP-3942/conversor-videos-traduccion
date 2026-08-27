# TTS sincronizado

La generación TTS es opcional y está desactivada por defecto. Cuando se activa, el pipeline utiliza el VTT traducido que exista en la carpeta de salida como fuente de verdad. Si ese archivo ha sido corregido previamente por el flujo de QA, el TTS utiliza directamente esa versión corregida.

## Flujo

```text
Audio
  ↓
Whisper + timestamps de palabra
  ↓
separación de pausas largas
  ↓
VTT original
  ↓
traducción conservando timestamps
  ↓
QA/corrección sin cambiar timing
  ↓
TTS por cue
  ↓
audio colocado en su timestamp
  ↓
WAV completo con silencios
  ↓
MP4 TTS + WebM TTS
```

Whisper utiliza `word_timestamps=true` para detectar pausas internas. Por defecto una separación de al menos `1500 ms` crea cues independientes. Esto evita mantener visible la última frase durante una pausa larga. El umbral se configura con `whisper_min_silence_duration_ms` o `WHISPER_MIN_SILENCE_DURATION_MS`.

No se genera un único audio continuo a partir de todo el texto. Cada cue conserva `start/end`; los silencios entre cues se mantienen y los solapamientos del VTT se rechazan.

## Proveedor local

La implementación inicial usa **Kokoro-82M mediante `kokoro-onnx`**. El paquete se carga de forma diferida, por lo que una instalación sin el extra `tts` continúa funcionando como antes.

Instalación:

```bash
python -m pip install ".[tts]"
```

Hay que colocar fuera del repositorio los pesos configurados en:

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

`required = false` significa que un fallo de TTS no invalida los resultados tradicionales. Para una ejecución en la que el doblaje sea obligatorio se puede cambiar a `true`.

También existen equivalentes mediante variables `TTS_*` para instalaciones desatendidas.

## Sincronización

Si un cue ocupa `10.000 → 14.500`, su audio se coloca en ese intervalo. Cuando el TTS supera el espacio disponible se intenta una segunda síntesis con velocidad superior, limitada por `max_speed`. Si aun así no cabe dentro de la tolerancia configurada, el cue falla en lugar de solapar el siguiente.

Los timestamps inválidos, cues vacíos y solapamientos se tratan explícitamente. Los cues vacíos producen silencio.

## Artefactos

La nomenclatura mantiene el stem normalizado existente y añade el sufijo TTS:

```text
<stem>_tts.mp4
<stem>_tts.webm
<stem>_tts.wav
```

El WAV es un artefacto auxiliar útil para inspección y remezcla. Los resultados de vídeo son los artefactos destinados al consumo normal.

El MP4 conserva el vídeo existente y codifica la narración como AAC. Para WebM se reutiliza el WebM normal existente cuando está disponible y se codifica el audio como Opus. Así se evita recodificar innecesariamente el vídeo.

## Resume e idempotencia

El decorador de storage se ejecuta en el mismo núcleo de almacenamiento que usa el pipeline. Un artefacto TTS ya válido no se vuelve a sintetizar. Los fallos se registran en el manifest y un fallo obligatorio impide finalizar la fuente.

El manifest registra, cuando existe, `tts_mp4`, `tts_webm`, `tts_cue_count`, `tts_adjusted_cues` y `tts_status`.

## Cloud y rclone

No se generan implementaciones independientes para Google Drive, rclone y almacenamiento local. El decorador descarga temporalmente el vídeo/VTT desde el backend, ejecuta el mismo generador TTS y vuelve a subir los artefactos al mismo directorio.

La fuente no se elimina por la capa TTS. La eliminación/archivo de fuentes continúa siendo responsabilidad del proveedor de almacenamiento existente, por lo que un fallo de subida TTS no borra el vídeo de origen.

## Ejecutable y tareas programadas

Los pesos no se incluyen automáticamente en PyInstaller. Deben estar en `tools/tts/` de la distribución portable o en rutas externas configuradas con `TTS_MODEL_PATH` y `TTS_VOICES_PATH`. Esto evita crear un binario innecesariamente grande y permite actualizar pesos sin recompilar.

`run_local`, Task Scheduler y `launchd` continúan invocando el mismo `main.py`/ejecutable y, por tanto, el mismo pipeline.

## Licencias

| Componente | Licencia/restricción relevante |
|---|---|
| `kokoro-onnx` | MIT |
| Modelo Kokoro-82M | Apache-2.0 |
| `onnxruntime` | MIT |
| `numpy` | BSD-3-Clause |

La cadena TTS debe revisarse completa antes de redistribuir un ejecutable comercial. En particular, las dependencias transitivas de fonemización y sus datos/voces deben conservar sus avisos y condiciones. Esta PR no afirma compatibilidad legal automática con una distribución propietaria cerrada.

## Limitaciones

- No se incluyen pesos del modelo en Git.
- La generación real con Kokoro requiere instalar `[tts]` y disponer de ambos pesos.
- La calidad lingüística depende del idioma/voz elegidos.
- Para distribución comercial cerrada, la cadena de dependencias TTS debe revisarse antes de empaquetar el ejecutable.