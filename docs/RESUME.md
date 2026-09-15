# Resume e idempotencia

El pipeline está diseñado para reutilizar artefactos completados y válidos en lugar de repetir procesos costosos.

Conceptualmente:

```text
artefacto ausente → ejecutar etapa
artefacto no válido → regenerar etapa
artefacto válido → reutilizar etapa
```

`resume_enabled` tiene `true` como valor predeterminado. `--no-resume` desactiva el comportamiento normal de resume para una ejecución y debe utilizarse únicamente para reprocesamientos deliberados.

Los manifests y el registro de procesados realizan el seguimiento del estado de salida. Un bloqueo de runtime evita que ejecuciones simultáneas corrompan el estado compartido.

## Recuperación de subtítulos

La reparación de subtítulos es más selectiva que una ejecución completa:

- VTT original no válido/ausente → STT de nuevo y después traducción;
- VTT original válido + VTT traducido no válido/ausente → solo traducción;
- ambos no válidos → STT una vez y después traducción.

La reparación de subtítulos no regenera el vídeo normal.

## TTS

Un artefacto TTS existente y válido puede reutilizarse. Si la reparación de subtítulos modifica el VTT utilizado por TTS, debe regenerarse la salida TTS correspondiente para mantener consistentes el texto y la temporización.
