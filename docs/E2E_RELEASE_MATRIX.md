# Release 1.4.1 — Matriz E2E

La suite E2E de la release utiliza ejecución real de subprocesos, almacenamiento local temporal, adaptadores de prueba deterministas para las fronteras externas de STT/traducción, el `MediaPipeline` real y ffmpeg. Google Drive y rclone se representan mediante su contrato público `StorageProvider` en pruebas aisladas; no se requieren credenciales de producción.

| Caso de uso | Script / punto de entrada | Resultado esperado | Validación |
| --- | --- | --- | --- |
| Procesamiento normal | `video-translation-pipeline run` / `scripts/run_local.*` | success | E2E del pipeline local real |
| Dry run | `video-translation-pipeline run --dry-run` | sin efectos secundarios | subproceso real |
| Concurrencia AUTO | `video-translation-pipeline run --dry-run --parallel-videos 0` | concurrencia efectiva segura | subproceso real |
| Concurrencia explícita | `video-translation-pipeline run --dry-run --parallel-videos 1` | exactamente 1 | regresión CLI/recursos |
| Concurrencia excesiva | `video-translation-pipeline run --dry-run --parallel-videos 999` | limitada por debajo de la solicitud | subproceso real |
| Resume | `video-translation-pipeline run` | reutilizar artefactos válidos | suite de regresión del pipeline |
| Resume con artefacto no válido | `video-translation-pipeline run` | reprocesar el artefacto no válido | suite de regresión del pipeline |
| Regeneración correcta | `scripts/run_local.sh regenerate` | nuevo resultado válido, copia de seguridad eliminada | E2E real del wrapper de subproceso |
| Fallo de regeneración | `video-translation-regenerate` | restaurar el resultado anterior | E2E real del punto de entrada |
| CLI TTS | `video-translation-tts --help` | punto de entrada ejecutable | validación de paquete limpio |
| Ejecución programada | `scripts/run_scheduled.*` / `video-translation-pipeline run --scheduled` | mismo punto de entrada del pipeline común | dry-run de subproceso real |
| Ejecutable independiente programado | `video-translation-scheduled` | no compatible con el paquete actual | NO APLICABLE |
| Almacenamiento local | pruebas existentes del pipeline/proveedor | success | pruebas del proveedor |
| Fallo de almacenamiento | pruebas existentes del proveedor | fallo correcto | pruebas del proveedor |
| Contrato de almacenamiento remoto | contratos públicos de proveedores Google/rclone | mismo contrato de backup/restore/delete | pruebas de contrato |
| Duplicados | pipeline normal | omitir/reutilizar correctamente | suite de regresión |
| Traducción parcial | pipeline normal | estado parcial | suite de regresión |
| Limpieza | pipeline común | sin residuos inseguros | suite de regresión |

## Frontera de integración de scripts

`run_local.sh` y `run_local.bat` son wrappers de ejecución. La acción `regenerate` se deriva directamente a `src.regeneration`; la regeneración se encarga de la orquestación e invoca `MediaPipeline`, que utiliza el contrato público `StorageProvider`. Los wrappers no implementan procesamiento multimedia, almacenamiento, rollback ni lógica de concurrencia.

## Frontera E2E

Las pruebas E2E de subprocesos sustituyen únicamente los adaptadores externos de STT y traducción por adaptadores de prueba deterministas. `MediaPipeline`, el proveedor de almacenamiento local, la extracción, la conversión multimedia con ffmpeg, la gestión de manifests, la orquestación de regeneración, los puntos de entrada CLI y los wrappers de ejecución relevantes siguen siendo reales. Esto mantiene la suite determinista sin descargas de modelos, claves API, hardware GPU ni acceso a Internet.

La ejecución de archivos `.bat` de Windows no puede certificarse desde un runner Linux y debe marcarse como NO VALIDADA salvo que exista un entorno de ejecución Windows disponible.
