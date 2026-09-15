# Pipeline de procesamiento

El pipeline común procesa cada entrada mediante etapas que pueden recuperarse de forma independiente. Cuando se procesan varios vídeos en una ejecución, el runtime determina la concurrencia efectiva de vídeo antes de crear los workers.

```text
vídeo de entrada / ZIP
      ↓
validación + extracción
      ↓
normalización multimedia
      ↓
STT + segmentación sensible a silencios
      ↓
validación del VTT original
      ↓
traducción
      ↓
validación del VTT traducido
      ├── subtítulos / vídeo normal
      └── TTS opcional
              ↓
          audio de cada cue
              ↓
          MP4/WebM TTS
              ↓
       validación de artefactos
              ↓
           manifest
```

Las etapas exactas que se reutilizan u omiten dependen de los artefactos existentes válidos y de la política de resume configurada.

## Concurrencia de vídeo

Para el procesamiento concurrente de vídeo, `max_parallel_videos` se trata como un límite superior. En la implementación actual de `main`, `0` significa AUTO: el runtime resuelve la configuración efectiva de Whisper y deriva un límite conservador de concurrencia a partir de la CPU y la RAM disponible, considerando también la memoria de GPU cuando se selecciona CUDA. Un valor positivo configurado puede limitarse a ese techo, mientras que `1` mantiene la ejecución con un único worker.

Esta planificación consciente de los recursos de los workers de vídeo se introdujo después de la release publicada `1.2.2` mediante la PR #20. Por tanto, forma parte del comportamiento actual de `main` y no debe atribuirse retroactivamente a la release `1.2.2`.

## Invariante temporal

Cada cue de subtítulo generado debe cumplir `start < end`. La traducción modifica el texto del cue, pero conserva `start`/`end`. TTS utiliza el VTT traducido y validado como fuente temporal y conserva los intervalos como silencio.

## Fallos y recuperación

- Los artefactos ausentes/no válidos son candidatos a regeneración.
- Los artefactos válidos se reutilizan cuando la etapa lo permite.
- La reparación de subtítulos no regenera el vídeo normal.
- Un fallo de TTS no elimina artefactos válidos del vídeo normal ni de los subtítulos.
- Un bloqueo de runtime impide ejecuciones simultáneas del pipeline.
