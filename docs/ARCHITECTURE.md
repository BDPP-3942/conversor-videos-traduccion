# Arquitectura

La aplicación utiliza un pipeline de procesamiento común con adaptadores intercambiables de almacenamiento y proveedores. La concurrencia de vídeo se resuelve a partir de la configuración efectiva de Whisper y del hardware detectado antes de que el pipeline cree los workers.

```text
CLI / wrappers / ejecutable / scheduler
                  │
                  ▼
          cargador de configuración
                  │
                  ▼
       resolución de Whisper/recursos
       presupuesto de CPU + RAM + GPU opcional
                  │
                  ▼
       paralelismo efectivo de vídeo
                  │
                  ▼
          MediaPipeline común
          ┌───────┼────────┐
          ▼       ▼        ▼
         STT   traducción  TTS
          │       │        │
          └───────┼────────┘
                  ▼
        validación de artefactos
                  │
                  ▼
          adaptador de almacenamiento
      ┌───────────┼───────────┐
      ▼           ▼           ▼
    local     Google Drive   rclone
```

## Componentes principales

- `main.py`: análisis de argumentos de la CLI, comprobaciones de disponibilidad, logging, bloqueo de ejecución y orquestación.
- `config/`: configuración TOML/entorno y resolución de rutas.
- `src/pipeline.py`: flujo común de procesamiento multimedia.
- `src/stt_engine.py`: transcripción con `faster-whisper`.
- `src/resource_profile.py`: detección de hardware/recursos, resolución de Whisper y concurrencia segura de vídeo.
- `src/file_naming.py`: normalización compartida de nombres lógicos/físicos y aplicación de límites de la frontera del sistema de archivos.
- `src/naming_policy.py`: inferencia de metadatos de curso/lección y raíces lógicas de salida.
- `src/archive_naming.py`: interpretación de nombres ZIP utilizada por la política de nombres.
- `src/subtitle_qa.py` y `src/subtitle_repair.py`: validación/reparación de subtítulos.
- `src/translator.py` y `src/translation_providers.py`: orquestación y proveedores de traducción.
- `src/tts_pipeline.py`: TTS sincronizado a nivel de cue.
- `src/storage/`: abstracción de almacenamiento e implementaciones locales/en la nube.
- `src/manifest.py`, `src/storage/processed_registry.py`: estado y seguimiento de resultados procesados.
- `src/output_deduplicator.py`: análisis/eliminación conservadora de duplicados.
- `src/auth/`: OAuth de Google, gestión de rclone y comprobaciones de disponibilidad para ejecución desatendida.

## Frontera de nombres y sistema de archivos

Los nombres tienen dos etapas explícitas. `naming_policy` deriva la identidad lógica del curso/recurso a partir del ZIP y del contexto de origen; después `file_naming` convierte ese componente en la representación física del sistema de archivos. Esto impide que un nombre lógico pueda eludir las comprobaciones finales de seguridad de la plataforma.

El contrato físico es:

```text
<curso_o_contenedor>x<nombre_sanitizado>
```

`x` es el separador de ámbito y `_` el separador interno de palabras. La normalización física es determinista: Unicode se descompone canónicamente con NFD, se eliminan las marcas diacríticas combinantes y se recompone con NFC; los espacios y guiones separadores se convierten en `_`; la puntuación incompatible y los caracteres de control se eliminan/reemplazan; los nombres reservados de Windows quedan protegidos; y se aplican los límites de longitud del sistema de archivos. Esto produce deliberadamente formas basadas en letras como `Café` → `cafe` y `Niño` → `nino`, en lugar de depender de una transliteración heurística.

Los metadatos lógicos permanecen separados del nombre físico, y la extracción ZIP rechaza las colisiones NFC/insensibles a mayúsculas y minúsculas antes de escribir. Así, el pipeline mantiene un único contrato Unicode desde la entrada del archivo comprimido hasta el artefacto generado en el sistema de archivos.

La política de nombres está cubierta por casos funcionales específicos; la frontera física final aplica la política multiplataforma de todo el proyecto.

La extracción ZIP realiza su propia validación de seguridad antes de escribir, incluyendo traversal, rutas absolutas/UNC, enlaces simbólicos, componentes reservados y colisiones Unicode/insensibles a mayúsculas y minúsculas. Las carpetas y artefactos de salida generados pasan después por la misma frontera de nombres físicos.

## Concurrencia consciente de los recursos

El runtime resuelve el dispositivo/modelo efectivo de Whisper y estima un presupuesto conservador de recursos antes de calcular la concurrencia de vídeo. El cálculo considera los hilos de CPU, la RAM disponible y la memoria de GPU cuando se selecciona CUDA, reservando margen para el sistema operativo, el runtime de Python y FFmpeg.

`max_parallel_videos = 0` significa AUTO. Los valores positivos representan la concurrencia máxima solicitada y pueden limitarse al techo seguro del hardware configurado. Un valor configurado de `1` mantiene un único worker.

Este comportamiento de concurrencia consciente de los recursos se introdujo después de la release `1.2.2` mediante la PR #20. Por tanto, forma parte de la arquitectura actual de `main`, pero no de la release publicada `1.2.2`.

## Restricciones de diseño

1. La selección del almacenamiento no debe duplicar la lógica de negocio.
2. La temporización VTT es el contrato temporal entre STT, traducción y TTS.
3. Los artefactos válidos son reutilizables; los artefactos inválidos o ausentes se regeneran selectivamente.
4. La ejecución programada no debe requerir autenticación interactiva.
5. Las operaciones de borrado deben ser conservadoras y volver a validar sus entradas.
6. La concurrencia de vídeo debe mantenerse dentro de un presupuesto conservador de recursos, en lugar de saturar ciegamente el equipo anfitrión.
7. Los metadatos de nombres lógicos deben seguir siendo distinguibles de los nombres físicos del sistema de archivos.
8. La normalización Unicode debe utilizar el pipeline documentado NFD → eliminación de marcas combinantes → NFC; la seguridad no debe depender de transliteración heurística ni de reparación de mojibake.
