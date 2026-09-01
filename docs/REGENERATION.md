# Regeneración completa de vídeos

## Semántica

La regeneración es una operación explícita y destructiva sobre los **artefactos derivados**, no sobre la fuente:

```text
fuente original
    ↓
localizar manifest/resultados existentes
    ↓
StorageProvider.backup_output_folder()
    ↓
MediaPipeline común con force_reprocess
    ↓
validación normal del pipeline
    ↓
StorageProvider.delete_output_backup()
```

Si el pipeline falla:

```text
fallo
  ↓
StorageProvider.restore_output_backup()
  ↓
restaurar manifest anterior
```

No equivale a `resume`. El modo normal mantiene la idempotencia, resume y deduplicación existentes.

## CLI

Después de instalar el paquete:

```bash
video-translation-regenerate --help
video-translation-regenerate
```

La regeneración reutiliza el contrato de opciones de `run` para las opciones que conservan exactamente la misma semántica en `MediaPipeline`.

### Opciones compartidas con `run`

| Flag | Valor / default | Aplicabilidad |
|---|---|---|
| `--provider` | `local`, `google_drive`, `gdrive` o `rclone` | Compartida. Selecciona el backend de almacenamiento y exige URIs compatibles. Si se omite usa el provider activo de configuración. |
| `--source` | URI | Compartida. Sustituye la fuente configurada; si se omite se usa la fuente activa. |
| `--target` | URI | Compartida. Sustituye el destino configurado; si se omite se usa el destino activo. |
| `--no-name-migration` | flag | Compartida. Desactiva la normalización de nombres heredados durante esta ejecución. |
| `--parallel-videos N` | entero; `0 = AUTO` | Compartida. Solicita el máximo de workers; se aplica el mismo cálculo seguro por hardware que en `run`. |
| `--translation-batch-size N` | entero | Compartida. Define el tamaño de lote de traducción; valores menores que 1 se normalizan al mínimo válido por el contrato común. |
| `--whisper-beam-size N` | entero | Compartida. Ajusta el beam size de Whisper; se aplica la misma normalización que en `run`. |
| `--whisper-cpu-threads N` | entero | Compartida. Ajusta los hilos CPU de Whisper; `0` mantiene la selección automática del runtime. |
| `--no-ffmpeg-copy` | flag | Compartida. Desactiva el intento de conservar streams mediante copy y fuerza la configuración de reencode correspondiente. |
| `--generate-webm` / `--no-webm` | flags mutuamente excluyentes | Compartidas. Fuerzan, respectivamente, la generación o no generación del WebM secundario. |

Las definiciones anteriores no se mantienen manualmente en dos parsers: regeneración reutiliza las acciones argparse de `run`, incluyendo tipo, choices, defaults y texto de ayuda, y reutiliza la misma función de aplicación de overrides.

### Opciones deliberadamente exclusivas de `run`

| Flag | Motivo |
|---|---|
| `--scheduled` | Es un modo de ejecución desatendida del comando `run`; la regeneración ya es un entry point explícito y no necesita cambiar su contrato mediante esta flag. |
| `--dry-run` | No existe un modo de regeneración que ejecute solamente readiness y omita la operación; aceptar la flag sin regenerar produciría una semántica distinta a `run`. |
| `--no-retain-sources` | Contradice una garantía fundamental de regeneración: la fuente original se conserva siempre. |
| `--no-resume` | La regeneración ya ejecuta `MediaPipeline.run(..., force_reprocess=True)`; aceptar esta flag sería redundante y podría sugerir una semántica de resume que no aplica. |

Las flags exclusivas de `run` se rechazan como argumentos desconocidos por el parser de regeneración; no se aceptan y se ignoran silenciosamente.

## Ejemplos

```bash
video-translation-regenerate \
  --provider local \
  --source local://storage/input \
  --target local://storage/output \
  --parallel-videos 1 \
  --translation-batch-size 10 \
  --whisper-beam-size 5 \
  --generate-webm
```

La configuración persistente sigue siendo la misma que utiliza el pipeline normal. Los overrides solo afectan a esta ejecución.

## Qué se conserva

- El ZIP/vídeo fuente nunca se elimina ni se mueve como consecuencia de la regeneración.
- Si la regeneración falla, los resultados anteriores se restauran cuando el proveedor permite rename.
- La regeneración utiliza `MediaPipeline`, por lo que no existe un pipeline audiovisual paralelo que omita STT, VTT, traducción, QA, TTS o generación audiovisual.

## Contrato de StorageProvider

La operación usa únicamente el contrato público del proveedor:

- `backup_output_folder(...)`: mueve un resultado existente a un backup gestionado por el provider.
- `restore_output_backup(...)`: restaura el backup si la ruta original está libre.
- `delete_output_backup(...)`: elimina el backup después del éxito.

Las operaciones concretas de filesystem, Google Drive o rclone permanecen dentro de sus adaptadores. La regeneración no accede a atributos privados del provider ni monkey-patchea `MediaPipeline`.

## Qué se invalida

Los folders de salida registrados por el manifest se retiran temporalmente antes de procesar. Esto incluye todos sus artefactos derivados: vídeos, VTT, TTS, audio, metadata y archivos auxiliares presentes dentro del folder.

El manifest nuevo se genera mediante la misma ruta que usa el procesamiento normal.

## Storage

### Local

El resultado anterior se renombra dentro del mismo filesystem. La regeneración procesa el nuevo resultado con el pipeline normal y elimina recursivamente el backup anterior solo después de una finalización `success`.

### Google Drive

Los folders anteriores se renombran dentro de Drive y, una vez completada la regeneración, el backup se elimina mediante la API de Drive. Esto no constituye una transacción ACID; si una operación distribuida falla, la recuperación depende del estado observado por el provider.

### rclone

Los backups se eliminan mediante `rclone purge` después de una regeneración exitosa. El backend rclone no proporciona aquí una transacción multi-operación; un fallo durante la publicación puede requerir intervención manual.

## Atomicidad y recuperación

La operación evita destruir inmediatamente el resultado anterior: primero crea un backup lógico mediante rename y solo lo elimina después del éxito completo.

Esto **no debe interpretarse como atomicidad distribuida**. Especialmente en Google Drive y rclone, renombrar, procesar, publicar y eliminar son operaciones independientes. El original se conserva, y los resultados anteriores pueden recuperarse si la fase de procesamiento falla antes de su limpieza definitiva.

## Concurrencia

La CLI utiliza el mismo `RunLock` global que la ejecución normal. Por tanto, dos ejecuciones completas no pueden competir simultáneamente desde los entrypoints que respetan ese lock.
