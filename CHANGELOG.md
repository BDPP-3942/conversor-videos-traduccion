# Changelog

## 2.6.0
- Añadidos modos explícitos `--mode local`, `--mode cloud` y `--mode rclone`.
- `run_local` permite seleccionar el modo directamente; por defecto sigue siendo local.
- `run_scheduled` usa Google Drive/cloud por defecto.
- El proveedor Google Drive mueve el ZIP procesado a `archive_folder_id` tras éxito para evitar reprocesados en ejecuciones programadas.
- El modo cloud mantiene FFmpeg/Whisper/traducción en local, sube los resultados y elimina los temporales mediante `TemporaryDirectory`.
- Añadida variable `GDRIVE_ARCHIVE_FOLDER_ID` y `google_drive.archive_folder_id`.
- `setup_env --cloud` instala las dependencias Google; `setup_env --rclone` comprueba el ejecutable rclone.
- Rclone documentado correctamente como herramienta CLI externa, no como librería Python.


## 2.5.0
- Añadida inferencia conservadora de nombres textuales de curso y lección.
- Reconocimiento de marcadores `curso/course`, `lección/lesson`, `capítulo/chapter`, `clase`, `tema` y `unidad`.
- Priorización de números fiables sobre etiquetas textuales.
- Eliminación de ruido habitual de WeTransfer, Google Drive y compresores antes de inferir nombres.
- Los nombres textuales inferidos se normalizan con la política WordPress y el límite real del filesystem.
- Añadidas pruebas de regresión para cursos/lecciones textuales, ruido de descargas y no-inferencia de nombres arbitrarios.

## 2.4.0
- Reanudación paralela por vídeo con un máximo configurable de workers locales.
- Traducción por lotes mediante `deep-translator` con fallback individual por lote.
- Whisper optimizado por defecto para throughput: beam size 1, `best_of=1`, `temperature=0`, sin condicionamiento del texto anterior, VAD y sin word timestamps.
- Hilos de Whisper ajustables automáticamente por worker.
- MP4 ya compatibles: intento de remux/copia con `-c copy` y fallback a transcodificación H.264/AAC si falla.
- Migración de nombres antiguos: normalización WordPress + ajuste al límite real del filesystem + actualización de manifests.
- Nuevas opciones CLI para `parallel-videos`, batch de traducción, parámetros Whisper y copia FFmpeg.


## 2.3.0

- Añadida reanudación real por vídeo mediante manifests incrementales.
- Un vídeo solo se reutiliza si el manifest indica `success` y existen MP4, MP3, VTT traducido y VTT original.
- El manifest se actualiza después de cada vídeo para permitir recuperación tras interrupciones.
- Compatibilidad de lectura con manifests antiguos en formato de lista.
- Añadida migración automática de nombres antiguos Unicode/especiales a nombres ASCII compatibles con WordPress.
- La migración se aplica a carpetas y archivos locales y a los proveedores Google Drive/rclone cuando están disponibles sus operaciones correspondientes.
- Añadidas opciones `resume_enabled`, `normalize_legacy_names`, `--no-resume` y `--no-name-migration`.
- Se mantiene la finalización idempotente de fuentes desaparecidas y el tratamiento de `FileNotFoundError` como advertencia cuando ocurre después de un procesamiento correcto.
- Añadidas pruebas de regresión para reanudación, manifests antiguos y migración de nombres.
