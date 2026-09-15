# Subtítulos y WebVTT

WebVTT es el formato de intercambio de subtítulos entre STT, traducción, QA/reparación y TTS.

## Contrato temporal

El VTT original establece la temporización. La traducción conserva `start` y `end`; TTS utiliza el VTT traducido y validado sin desplazar los cues posteriores.

Un cue válido debe tener `start < end`, marcas de tiempo ordenadas y sintaxis WebVTT válida. Los intervalos entre cues son válidos y representan silencio; no se rellenan automáticamente.

## QA y reparación

El proyecto incluye `src.subtitle_qa` y el punto de entrada `video-subtitle-qa` para el diagnóstico de subtítulos. La capa de reparación gestiona artefactos VTT históricos ausentes/no válidos.

Reglas de recuperación:

1. VTT original no válido/ausente → volver a ejecutar STT, validar y después traducir;
2. original válido + traducción no válida/ausente → conservar la temporización original y volver a ejecutar la traducción;
3. ambos no válidos → volver a ejecutar STT una vez, validar y después traducir.

Los archivos VTT existentes se guardan como copia de seguridad antes de sustituirlos. Un VTT válido no se regenera innecesariamente.

## Convenciones de salida

La salida puede contener una transcripción original bajo `original_transcriptions/` y un VTT traducido cuyo nombre depende del idioma de destino configurado. No codifiques un sufijo de idioma en las herramientas operativas; inspecciona la salida generada o la configuración.
