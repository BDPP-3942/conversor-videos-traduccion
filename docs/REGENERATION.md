# Regeneración completa de vídeos

## Semántica

La regeneración es una operación explícita y destructiva sobre los **artefactos derivados**, no sobre la fuente:

```text
fuente original
    ↓
localizar manifest/resultados existentes
    ↓
renombrar temporalmente los resultados anteriores a backup
    ↓
forzar pipeline completo desde la fuente
    ↓
validar resultado
    ↓
publicar el resultado actual
    ↓
eliminar backups anteriores
```

No equivale a `resume`. El modo normal mantiene la idempotencia, resume y deduplicación existentes.

## CLI

Después de instalar el paquete:

```bash
video-translation-regenerate
```

También admite ubicaciones explícitas:

```bash
video-translation-regenerate \
  --source local://storage/input \
  --target local://storage/output
```

La configuración del proveedor activo sigue siendo la misma que utiliza el pipeline normal.

## Qué se conserva

- El ZIP/vídeo fuente nunca se elimina ni se mueve como consecuencia de la regeneración.
- Si la regeneración falla, los resultados anteriores se restauran cuando el proveedor permite la operación de rename.
- La regeneración utiliza `MediaPipeline`, por lo que no existe un pipeline paralelo que omita STT, VTT, traducción, QA, TTS o generación audiovisual.

## Qué se invalida

Los folders de salida registrados por el manifest se retiran temporalmente antes de procesar. Esto incluye todos sus artefactos derivados: vídeos, VTT, TTS, audio, metadata y archivos auxiliares presentes dentro del folder.

El manifest nuevo se genera mediante la misma ruta que usa el procesamiento normal.

## Storage

### Local

El resultado anterior se renombra dentro del mismo filesystem. La regeneración procesa el nuevo resultado con el pipeline normal y elimina recursivamente el backup anterior solo después de una finalización `success`.

### Google Drive

Los folders anteriores se renombran dentro de Drive y, una vez completada la regeneración, se envían a la papelera mediante la API de Drive. Esto es recuperable desde la papelera de Drive, pero no constituye una transacción ACID.

### rclone

Los backups se eliminan mediante `rclone purge` después de una regeneración exitosa. El backend rclone no proporciona aquí una transacción multi-operación; un fallo durante la publicación puede requerir intervención manual.

## Atomicidad y recuperación

La operación evita destruir inmediatamente el resultado anterior: primero crea un backup lógico mediante rename y solo lo elimina después del éxito completo.

Esto **no debe interpretarse como atomicidad distribuida**. Especialmente en Google Drive y rclone, renombrar, procesar, publicar y eliminar son operaciones independientes. El original se conserva, y los resultados anteriores pueden recuperarse si la fase de procesamiento falla antes de su limpieza definitiva.

## Limitación conocida

El contrato histórico de `StorageProvider` no expone todavía una operación pública `delete_folder`. La implementación actual mantiene la mecánica destructiva en un adaptador específico de regeneración para no modificar el core del pipeline. Una evolución posterior recomendable es promover `delete_folder` a la interfaz de storage y cubrir sus garantías por proveedor.

## Concurrencia

La CLI utiliza el mismo `RunLock` global que la ejecución normal. Por tanto, dos ejecuciones completas no pueden competir simultáneamente desde los entrypoints que respetan ese lock.
