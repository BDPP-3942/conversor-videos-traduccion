# Recuperación y validación de VTT

## Fuente de verdad temporal

El VTT original generado por STT define los intervalos temporales. La traducción debe conservar `start` y `end`; no se permite que el traductor invente o modifique el timing.

Un cue es válido cuando:

- `start >= 0`;
- `end > start`;
- los cues están ordenados temporalmente;
- no existe un solapamiento temporal inesperado;
- el fichero es sintácticamente válido como WebVTT.

Un cue con `start >= end` es inválido y no debe llegar a reproducción ni a TTS.

## Por qué aparecen errores históricos

La segmentación por silencios utiliza timestamps de palabra de Whisper. Los resultados antiguos pueden proceder de una versión anterior del pipeline o de un artefacto que no aplicó la validación final. El código actual valida de nuevo los segmentos después de dividirlos.

## Tres casos de recuperación

### 1. VTT original/STT inválido

Si existe el vídeo normal pero el VTT original contiene timestamps imposibles, se vuelve a ejecutar STT sobre ese vídeo. No se vuelve a convertir el vídeo ni se modifica el MP4 normal.

```text
MP4 existente
   ↓
STT
   ↓
VTT original válido
```

### 2. VTT de traducción inválido

Si el VTT original es válido pero la traducción tiene timestamps inválidos, se vuelve a traducir usando los segmentos originales. Los timestamps se conservan desde STT.

```text
VTT original válido
   ↓
traducción
   ↓
VTT traducido válido
```

### 3. Ambos VTT son inválidos

Se regenera primero el STT desde el vídeo y, una vez validado, se regenera la traducción.

```text
MP4 existente
   ↓
STT
   ↓
VTT original
   ↓
traducción
   ↓
VTT traducido
```

En los tres casos se conservan copias de los VTT sustituidos con un sufijo `.bak.<timestamp>`.

## Reprocesado

Para todos los resultados existentes:

```bash
python main.py reprocess-subtitles --all --stt-only
python main.py reprocess-subtitles --all --translate-only
python main.py reprocess-subtitles --all
```

`--translate-only` puede recuperar automáticamente el STT cuando el VTT original no es válido, siempre que exista un vídeo reutilizable.

El reprocesado no regenera el vídeo normal.

## Integración con `run`

Una ejecución normal comprueba los resultados de salida cuando `TTS_ENABLED=true`. Antes de TTS:

1. valida el VTT original;
2. lo regenera desde el vídeo si es necesario;
3. valida el VTT traducido;
4. vuelve a traducir si es necesario;
5. genera TTS solo con un VTT válido.

Esto permite que el mismo mecanismo funcione tanto en la primera ejecución como sobre carpetas que ya contienen MP4 procesados.

## Reglas de seguridad

Nunca se debe solucionar `start >= end` simplemente cambiando `end` a un valor inventado. Si el timing no puede recuperarse de forma fiable, se debe regenerar STT a partir del vídeo existente.

Un VTT inválido no debe marcarse como resultado válido, utilizarse para TTS ni eliminar el artefacto anterior antes de haber generado y validado el sustituto.
