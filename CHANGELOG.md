# Changelog

## [1.8.3] — Release candidate

**Estado:** CANDIDATA — corrección multiplataforma del mecanismo de resolución de `uv`, pendiente de CI/Release Gate y publicación del tag `v1.8.3`.

**Baseline publicado:** `v1.8.2`. Esta release añade exclusivamente la corrección de resolución de `uv` en los consumidores del bootstrap gestionado por el proyecto.

**Nota de alcance:** la aplicación de escritorio y su infraestructura de empaquetado implementadas en la rama de trabajo son funcionalidad nueva y no forman parte de la release PATCH `1.8.3`. Si se conserva esta capacidad en `main`, deberá publicarse en la siguiente release MINOR (actualmente `1.9.0`) con la actualización completa de metadatos y `uv.lock` exigida por `docs/VERSIONING.md`.

### Fixed

- Añadido un resolvedor POSIX compartido que prioriza `tools/uv/uv` y usa `uv` de `PATH` como fallback.
- Añadido el resolvedor Windows equivalente, que prioriza `tools\\uv\\uv.exe` antes de `PATH`.
- Corregidos `run_local.*`, `run_unattended.*`, `setup_rclone.*`, `setup_google.*` y los scripts de build para consumir el ejecutable resuelto.
- Conservada la prioridad de ejecutables empaquetados en los wrappers unattended y el fallback directo a `.venv` Python cuando uv no está disponible.
- Eliminada la dependencia accidental de una instalación global de uv para ejecutar un checkout correctamente preparado por `setup_env.*`.

### Tests / CI

- Añadida `tests/test_uv_resolution_contract.py` con cobertura de los contratos POSIX y Windows.
- Verificada la precedencia de `tools/uv/` sobre `PATH`.
- Verificado que los wrappers y builds no vuelvan a exigir `command -v uv` o `where uv.exe` como precondición global.
- Conservada la matriz CI Linux/Windows/macOS y Python 3.11/3.12/3.13.

### Documentation

- Añadida la documentación específica de la resolución compartida de `uv` sin eliminar el historial de releases anteriores.
- Documentado el límite de versión que impide publicar la nueva aplicación de escritorio dentro de `1.8.3`.

### Compatibility

- PATCH compatible con la línea `1.8.x`.
- No cambia el pipeline audiovisual ni los contratos públicos de CLI, almacenamiento o formatos.

## [1.8.2] — MADLAD model download and Hugging Face revision fix

**Tipo:** PATCH — release publicada.

**Estado:** PUBLICADA — tag `v1.8.2`.

**Commit/tag de referencia:** `0165f7fdd000c0f29c8a022fa26a452afc55111c` / `v1.8.2`.

### Fixed

- Corregida la revisión fijada de MADLAD-400 3B CT2 INT8 a `fd0b55729c074372eb84b52b9309a00dc65c40c4`.
- Corregido el nombre del tokenizer: el artefacto real es `spiece.model`, no `sentencepiece.model`.
- Conservada la validación de tamaño y SHA-256 de los artefactos gestionados.
- Mejorado el diagnóstico de descargas de Hugging Face para distinguir un `404` de archivo/revisión inexistente de los errores de autenticación/autorización `401/403`.
- Corregidos los fixtures de tests de MADLAD para que los tamaños declarados coincidan con los bytes escritos.
- Alineados los metadatos de aplicación, packaging y documentación con la release `1.8.2`.

### Tests / CI

- Añadidas/regresadas pruebas para la revisión fijada, `spiece.model`, integridad, prefijo de destino MADLAD y diagnóstico de `404`.
- Mantenida cobertura independiente para OPUS-MT y su revisión fijada.
- Release Gate validado antes de publicar `v1.8.2`.

### Compatibility

- Release PATCH compatible sobre `1.8.1`.
- No cambia el pipeline audiovisual ni los contratos públicos de CLI, almacenamiento o formatos.
- La corrección se limita al recurso MADLAD, su validación, diagnóstico y documentación asociada.

## [1.8.1] — Local uv Bootstrap & Optional Local Translation Setup

**Tipo:** PATCH — release publicada.

**Estado:** PUBLICADA — tag `v1.8.1`.

**Commit/tag de referencia:** `a4a5b9143d6fe6d61b9780220394189ef88c25ec` / `v1.8.1`.

### Bootstrap automático de uv

- Los scripts de creación del entorno ya no requieren que `uv` esté instalado previamente en el sistema.
- Se reutiliza primero una copia gestionada por el proyecto en `tools/uv/`.
- Si no existe, se utiliza `uv` disponible en `PATH`.
- Si tampoco existe, el instalador oficial de uv crea automáticamente una copia local bajo `tools/uv/`.
- El bootstrap local no modifica los perfiles de shell del usuario.
- Se mantiene el comportamiento equivalente en macOS/Linux y Windows.
- El binario local de uv no se versiona en Git.

### Instalación opcional del modelo local

- Añadida la opción `--local-translation` a los scripts de setup para preparar durante el mismo proceso el modelo local de traducción fijado por el proyecto.
- La descarga continúa siendo opt-in porque MADLAD-400 3B ocupa aproximadamente 2.95 GB.
- Se conserva la vía independiente `uv run python scripts/manage_local_translation.py download` para diferir la descarga.
- Se mantienen los comandos de `status` y benchmark del modelo local.

### Versionado y documentación

- Proyecto y configuración actualizados a `1.8.1`.
- `uv.lock` sincronizado con la nueva versión.
- Actualizadas las instrucciones de instalación, migración y uso de uv y el README.
- Añadidas regresiones para los contratos de los scripts de instalación.

### Compatibility

No se modifican el pipeline de procesamiento audiovisual, los contratos de almacenamiento, los formatos de entrada/salida, los modelos locales y sus revisiones fijadas, la cadena de proveedores de traducción, el runtime CUDA/NVIDIA ni la interfaz existente de `manage_local_translation.py`.

### Validation

- CI multiplataforma sobre Linux, Windows y macOS con Python 3.11, 3.12 y 3.13.
- pytest, Ruff lint/format, comprobaciones de seguridad y `compileall`.
- `uv lock --check` y `uv pip check`.
- Auditorías de dependencias, packaging, construcción de distributions e instalación limpia del wheel.
- Release Gate validado antes de publicar `v1.8.1`.

## [1.8.0] — Whisper Recovery & Local Translation

**Tipo:** MINOR — release publicada.

**Estado:** PUBLICADA — tag `v1.8.0`.

### Scope

- Refinada la recuperación selectiva de segmentos sospechosos de Whisper, con reintento sin prompt inicial ni contexto de texto previo.
- Separados el silencio VAD (`2000 ms`) y la división de subtítulos (`1000 ms`).
- Conservado el contrato numérico de `clip_timestamps` durante la recuperación.
- Incorporado MADLAD-400 3B CT2 INT8 como modelo local predeterminado, manteniendo OPUS-MT como alternativa ligera.
- Añadida validación específica de integridad, tokenización, revisiones fijadas y presupuesto de instalación del modelo MADLAD.
- Reforzadas las regresiones de modelos locales, selección explícita de OPUS-MT y aislamiento de los tests de configuración frente a overrides del entorno.
- Actualizado el contexto de Whisper para vocabulario de Tai Chi.
- Cambiada la voz TTS predeterminada a `am_michael` y desactivada la generación WebM por defecto.
- Conservada la base de desarrollo, CI, build y auditoría con `uv` introducida por PR #42.

### Validation

La release `1.8.0` fue validada mediante CI multiplataforma, Release Gate, packaging y validación del lockfile sobre el SHA final publicado.

## [1.7.4] — Local translation shared vocabulary validation

**Tipo:** PATCH — release publicada.

### Fixed

- Corregida la validación de `shared_vocabulary.json` del modelo CTranslate2 local.
- `shared_vocabulary.json` puede tener una raíz JSON de tipo array, que es la estructura real del artefacto fijado `Prukario/opus-mt-es-en-ct2-int8@ad91ad1697ea1761111ff4c179400796d085b347`.
- Se mantiene la validación estricta de raíz objeto y claves obligatorias para `config.json` y `tokenizer_config.json`.
- La descarga desde cero del modelo ya puede completar la validación y activar el directorio gestionado del modelo local.

### Tests

- Añadida regresión específica para aceptar un `shared_vocabulary.json` con raíz array.
- Añadida regresión para rechazar `shared_vocabulary.json` con JSON inválido.
- Actualizados los fixtures de descarga y carga del proveedor para representar la estructura real del vocabulario compartido.
- CI multiplataforma validada sobre Linux, Windows y macOS con Python 3.11, 3.12 y 3.13.

### Compatibility

- No cambian el modelo ni la revisión fijados.
- No cambian los hashes ni tamaños esperados de `model.bin`, `source.spm` y `target.spm`.
- No cambia la configuración pública del proveedor de traducción local.
- Se conserva íntegramente la corrección de metadatos empaquetados introducida en `1.7.3`.

## [1.7.3] — Local translation model metadata bootstrap

**Tipo:** PATCH — release publicada.

### Fixed

- Añadidos al paquete los metadatos `config.json` y `tokenizer_config.json` correspondientes exactamente a la revisión fijada `Prukario/opus-mt-es-en-ct2-int8@ad91ad1697ea1761111ff4c179400796d085b347`.
- La preparación del modelo ya no depende de una descarga independiente desde Hugging Face para esos dos JSON pequeños.
- El gestor instala los metadatos empaquetados en el directorio final del modelo antes de validar y activar el runtime.
- `shared_vocabulary.json` continúa descargándose y validándose como artefacto del modelo, ya que forma parte del contenido generado por CTranslate2 y no se duplica innecesariamente dentro del paquete Python.

### Tests

- Añadida una regresión que verifica que los metadatos JSON empaquetados están disponibles.
- Ajustada la regresión de descarga para comprobar explícitamente que los ficheros descargados son `model.bin`, `source.spm`, `target.spm` y `shared_vocabulary.json`, mientras que los dos metadatos pequeños proceden del paquete.
- Se mantiene la prueba de inicialización del proveedor y traducción mediante CTranslate2 + SentencePiece.

### Packaging

- Añadido el subpaquete `config.local_translation_model` al artefacto Python para que los JSON necesarios estén presentes también en instalaciones empaquetadas.

### Compatibility

- No cambian el modelo/revisión fijados, la configuración pública ni el contrato de dependencias.
- Se conserva la corrección de descarga de `1.7.2` y la corrección `clip_timestamps` de `1.7.1`.

## [1.7.2] — Local translation model download fix

**Tipo:** PATCH — release publicada.

### Fixed

- Corregido el cálculo del límite de descarga de los ficheros del modelo local.
- Evitada la evaluación eager del fallback de `dict.get` que provocaba `KeyError: 'model.bin'` aunque `model.bin` estuviera correctamente definido en `MODEL_FILES`.
- La preparación vuelve a poder recorrer los tres ficheros principales (`model.bin`, `source.spm`, `target.spm`) y los metadatos JSON antes de validar y activar el modelo.

### Tests

- Añadida regresión que ejercita la descarga gestionada de todos los ficheros del modelo.
- Añadida regresión que prepara el modelo y comprueba la inicialización del proveedor y una llamada de traducción a través de CTranslate2 + SentencePiece.
- Se mantiene el benchmark real `scripts/benchmark_local_translation.py` como validación funcional del modelo fijado en el hardware objetivo.

### Documentation

- Actualizadas las instrucciones de preparación del modelo local y la explicación del fallo corregido.
- Actualizada la documentación de release y versionado para `1.7.2`.

### Compatibility

- No cambian el modelo/revisión fijados, la configuración pública, el pipeline audiovisual ni el contrato de dependencias.
- Se conserva la corrección `clip_timestamps` de `1.7.1`.

## [1.7.1] — STT selective recovery compatibility

**Tipo:** PATCH — release publicada.

### Fixed

- Corregido el contrato de `clip_timestamps` usado por la recuperación selectiva de `faster-whisper`: los intervalos se envían como valores temporales numéricos `[start, end]` en lugar de diccionarios.
- Añadidas pruebas de regresión que verifican el argumento recibido por `model.transcribe(...)`, la transcripción normal y la integración del resultado recuperado.

### Compatibility

- La revisión toma `v1.7.0` como baseline funcional inmediato y conserva sus capacidades de reprocessing/manifests, naming Unicode/filesystem y runtime de traducción local.
- Compatibilidad verificada con `faster-whisper>=1.2.1,<1.3`.

## [1.7.0] — Reprocessing, Unicode Naming & Translation Runtime

**Tipo:** MINOR — release publicada.

### Added / Improved

- Consolidado el procesamiento de reintentos y reprocesado de vídeos mediante `reprocess-subtitles`, incluyendo `stt_only`, `translate_only`, `full` y `reprocess_all`.
- Mejorada la persistencia y recuperación del estado de procesamiento mediante manifests, incluyendo escritura atómica y detección explícita de manifests corruptos o ilegibles.
- Reforzado el comportamiento multiplataforma del almacenamiento local para evitar condiciones de carrera relacionadas con la antigüedad de archivos y timestamps del filesystem.
- Consolidada la generación determinista de nombres de salida para vídeos, cursos y lecciones.
- Normalización Unicode estable mediante descomposición canónica NFD, eliminación de marcas diacríticas y recomposición NFC.
- Los nombres generados mantienen letras y números Unicode válidos, evitando transliteraciones arbitrarias y garantizando un comportamiento estable entre representaciones NFC/NFD.
- Reforzada la compatibilidad con las restricciones reales de los sistemas de archivos de Windows, Linux y macOS.
- Consolidada la protección frente a colisiones de nombres por mayúsculas/minúsculas y normalización Unicode.
- Mejorada la gestión de nombres y rutas que superan los límites del filesystem, incluyendo componentes Unicode cuyo tamaño debe calcularse en bytes UTF-8.

### Translation

- Consolidado el proveedor opcional de traducción local basado en CTranslate2 + SentencePiece.
- Mejorada la gestión del modelo local y su validación antes de ser utilizado.
- Añadida gestión configurable de la autenticación necesaria para descargar modelos privados o restringidos de Hugging Face.
- Los modelos públicos pueden prepararse sin necesidad de proporcionar credenciales.
- Mantenida la validación de integridad de los artefactos del modelo mediante tamaño y SHA-256.
- Consolidada la selección de dispositivo y `compute_type` para traducción local, manteniendo fallback conservador a CPU cuando GPU/CUDA no puede utilizarse correctamente.

### Filesystem & ZIP

- Consolidado el endurecimiento de extracción ZIP introducido en `v1.5.1`.
- Mantenida la protección frente a traversal mediante `/` y `\\`, rutas absolutas POSIX/Windows, rutas UNC, nombres reservados de Windows, entradas ZIP duplicadas, colisiones por case-folding, colisiones por normalización Unicode y entradas simbólicas.
- Preservada la estructura de directorios de los ZIP anidados y reforzada la normalización NFC de nombres de miembros y contenedores.

### Tests & Validation

- Ampliadas las regresiones de naming para nombres Unicode compuestos y descompuestos.
- Añadidas comprobaciones para eliminar diacríticos mediante normalización canónica sin transliteraciones selectivas.
- Ampliadas las pruebas de reprocessing, manifests, backups, restauración ante errores y validación de subtítulos.
- Mantenida la matriz multiplataforma de Linux, Windows y macOS con Python 3.11, 3.12 y 3.13.
- Validación mediante Ruff, Ruff Security, Ruff format, `compileall`, `pip check`, packaging, wheel e instalación limpia.
- Mantenidas las auditorías de dependencias y las validaciones del Release Gate.

### Compatibility

Esta es una release minor compatible con la arquitectura existente. No introduce una arquitectura alternativa de procesamiento.

## [1.6.0] — Local Translation & GPU Runtime Hardening

**Tipo:** MINOR — release publicada.

- Traducción local opcional, runtime CUDA gestionado, diagnóstico GPU/CPU y recuperación STT configurable.

## [1.5.1] — ZIP extraction and cross-platform filesystem hardening

**Tipo:** PATCH — release publicada.

- La extracción ZIP rechaza rutas absolutas POSIX/Windows, rutas UNC y traversal mediante separadores `/` o `\\`.
- Se rechazan componentes de ruta reservados por Windows.
- Se detectan colisiones de rutas antes de escribir cuando difieren únicamente por case o normalización Unicode.
- Las entradas ZIP duplicadas ya no pueden sobrescribir silenciosamente un archivo previamente extraído.

## [1.5.0] — Multiplatform Whisper, Context & Packaging

**Tipo:** MINOR — release publicada.

- Dispatcher común para `run_local.sh` y `run_local.bat`.
- Soporte coherente de `run` y `regenerate` mediante el `MediaPipeline` común.
- Política de naming y contexto externo para Whisper.
- CI multiplataforma y endurecimiento de wrappers.

## [1.4.2] — Regeneration CLI contract and help alignment

**Tipo:** MINOR — release publicada.

- Contrato CLI de regeneración alineado con `MediaPipeline`.
- Help público completado y regresiones de CLI añadidas.

## [1.4.1] — Corrective Script Integration

**Tipo:** PATCH — release publicada.

- Wrappers locales integrados con la regeneración existente sin duplicar lógica.

## [1.4.0] — Clean Video Regeneration and Release Hardening

**Tipo:** MINOR — release publicada.

- Regeneración limpia desde la fuente mediante el `MediaPipeline` común.
- Backup/restauración y endurecimiento de release, gobernanza y packaging.

## [1.3.0] — Safe Resource-Aware Video Concurrency

**Tipo:** MINOR — release publicada.

- Concurrencia automática basada en CPU/RAM/GPU con límites conservadores.

## [1.2.2] — Naming Timestamp Cleanup

**Tipo:** PATCH — release publicada.

- Eliminación de timestamps técnicos de nombres de curso/lección y resultados.

## [1.2.1] — TTS Installation Fix

**Tipo:** PATCH — release publicada.

- Corrección de instalación de assets TTS, especialmente en Windows.

## [1.2.0] — Naming and TTS Improvements

**Tipo:** MINOR — release publicada.

- Naming descriptivo determinista y bootstrap de assets Kokoro.

## [1.1.0] — Reparación de VTT e integración TTS en el pipeline

**Tipo:** MINOR — release publicada.

- Recuperación de VTT inválidos, regeneración controlada y TTS sincronizado en el pipeline común.

## [1.0.1] — Documentación de instalación y mantenimiento

**Tipo:** PATCH — release publicada.

- Añadida la guía de instalación y corregida la navegación documental.

## [1.0.0] — Primera release estable

Primera release estable del producto.
