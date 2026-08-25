# Deduplicación de resultados

La deduplicación de carpetas de salida se divide en tres fases independientes:

```text
scan → analyze → delete
```

`scan` y `analyze` nunca eliminan resultados. `delete` solo consume el plan persistido por `analyze` y vuelve a comprobar que el referente y el duplicado conservan exactamente la misma firma de contenido que cuando se analizaron.

## CLI

Por defecto se utiliza `storage/output`:

```bash
python main.py duplicates scan
python main.py duplicates analyze
python main.py duplicates delete --dry-run
python main.py duplicates delete
```

También puede indicarse otro directorio local:

```bash
python main.py duplicates --target "/ruta/absoluta/storage/output" scan
python main.py duplicates --target "/ruta/absoluta/storage/output" analyze
python main.py duplicates --target "/ruta/absoluta/storage/output" delete --dry-run
```

El orden recomendado es `scan`, `analyze`, revisión del plan y `delete`. El análisis queda en `storage/state/dedupe_plan.json` y el escaneo en `storage/state/dedupe_scan.json`.

## Política

Dos carpetas solo forman un grupo duplicado cuando contienen la misma firma SHA-256 de los recursos generados. Dentro del grupo se mantiene la política de estabilidad de nombres existente.

Solo se genera una decisión de borrado cuando el resultado más estable tiene una puntuación estrictamente superior al siguiente candidato. Si existe empate o no hay referente inequívoco, el grupo se conserva completo.

Antes del borrado se comprueba de nuevo:

- que el referente exista;
- que el duplicado exista;
- que nunca se intente borrar el referente;
- que ambas carpetas sigan teniendo la firma analizada;
- que la ruta del plan esté contenida directamente dentro del directorio de salida.

Si cualquiera de estas comprobaciones falla, el elemento se marca como `skipped` y no se borra.

## Estado y auditoría

Después de un borrado válido se eliminan del `media_registry.jsonl` las entradas correspondientes al resultado eliminado y se retiran del manifest las entradas cuyo `output_folder` ya no existe. Las operaciones retiradas quedan registradas en `storage/state/dedupe_history.jsonl`.

El procesamiento automático local mantiene el comportamiento existente: después de procesar el lote ejecuta `scan`, `analyze` y `delete`. Los comandos `duplicates` son independientes de ese flujo.
