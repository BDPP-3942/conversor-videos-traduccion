# Resumen del proyecto

## Propósito

**Video Translation Pipeline** es una aplicación Python orientada al procesamiento por lotes para la localización audiovisual. Acepta vídeos o paquetes ZIP, normaliza los medios, transcribe el habla, crea y valida subtítulos WebVTT, traduce sus segmentos conservando los tiempos y puede sintetizar narración sincronizada mediante Kokoro TTS.

Está diseñada para ejecución desatendida y admite almacenamiento local, Google Drive y rclone.

## Alcance

Las capacidades implementadas incluyen:

- ingestión de vídeos y ZIP;
- procesamiento multimedia mediante FFmpeg;
- STT con `faster-whisper`;
- segmentación basada en silencios y validación VTT;
- proveedores de traducción configurables con respaldo y reintentos;
- adaptadores local, Google Drive y rclone;
- manifests, reanudación/idempotencia y validación de artefactos;
- gestión conservadora de duplicados;
- TTS Kokoro sincronizado opcional;
- concurrencia adaptada a CPU, RAM y GPU disponible;
- CLI y ejecución desatendida;
- programación mediante los mecanismos de Windows, macOS y Linux;
- aplicación de escritorio multiplataforma y empaquetado nativo;
- pruebas, linting, seguridad, empaquetado y auditoría de dependencias.

La aplicación no es un editor audiovisual interactivo y los resultados automáticos de traducción/TTS requieren revisión humana cuando la exactitud sea crítica.

## Contrato de ejecución

El punto de entrada canónico es `main.py`. El paquete también expone `video-translation-pipeline`, `video-translation-regenerate`, `video-subtitle-qa`, `video-translation-tts` y `video-translation-desktop`.

En modo local, la aplicación de escritorio utiliza por defecto:

```text
Documentos/Video Translation Pipeline/input
                    ↓
                 pipeline
                    ↓
Documentos/Video Translation Pipeline/output
```

El estado interno, logs y cachés se mantienen separados en el directorio privado de datos de la aplicación. Las carpetas `input` y `output` pueden sustituirse por cualquier ubicación con permisos de escritura.

Consulta [`INSTALLATION.md`](INSTALLATION.md), [`CONFIGURATION.md`](CONFIGURATION.md), [`CLI.md`](CLI.md) y [`DESKTOP.md`](DESKTOP.md).

## Versionado e historial

El proyecto utiliza Semantic Versioning (`MAJOR.MINOR.PATCH`). Las versiones publicadas, sus tags y el alcance de cada release se documentan exclusivamente en [`RELEASES.md`](RELEASES.md) y [`CHANGELOG.md`](../CHANGELOG.md).

La documentación técnica de funcionalidades no depende de una versión concreta: describe el comportamiento general vigente del proyecto. Cuando un procedimiento necesite mostrar un valor específico, se indica como `<version>` o mediante el tag/versionado que corresponda al artefacto que se esté documentando.

El histórico general conserva las versiones desde `1.0.0` y distingue entre releases publicadas y candidatas sin eliminar anotaciones de versiones anteriores.

## Arquitectura funcional

```text
Entrada de vídeo / ZIP
        |
        v
Almacenamiento + extracción segura
        |
        v
Normalización de medios
        |
        v
STT / Whisper
        |
        v
VTT original + QA
        |
        v
Traducción + proveedores de respaldo
        |
        v
VTT traducido
        |
        +----> TTS Kokoro opcional
        |
        +----> WebM opcional
        |
        v
Resultados + manifest + estado de ejecución
```

La aplicación de escritorio, la CLI y los wrappers utilizan los mismos casos de uso y contratos del pipeline. La GUI no implementa un motor audiovisual alternativo.

## Almacenamiento

Los datos de trabajo del usuario y el estado privado de la aplicación están separados. `input` y `output` pueden estar en una carpeta local, compartida, de red o sincronizada siempre que el usuario tenga permisos de escritura.

Los manifests y mecanismos de reanudación permiten identificar resultados existentes y evitar procesamiento innecesario cuando los artefactos son compatibles.

## ZIP y Unicode

La extracción corrige de forma conservadora nombres UTF-8 que hayan sido interpretados como CP437 cuando falta el indicador UTF-8. La reparación de extracción y la normalización física posterior son capas distintas: un nombre legítimo como `niño` puede conservarse al extraer y convertirse después en `nino` por la política de nombres de salida.

La extracción también valida traversal, rutas absolutas/UNC, symlinks, nombres reservados de Windows, colisiones por normalización Unicode y colisiones por mayúsculas/minúsculas.

## Windows y distribución

La construcción de escritorio se realiza en la plataforma y arquitectura de destino. Un ejecutable x64 no puede ejecutarse en Windows x86.

El sistema de build acepta `x64` y `x86` como arquitecturas explícitas del MSI, pero una build x86 solo puede publicarse cuando Python, PyInstaller y todas las dependencias binarias requeridas por el pipeline estén disponibles y validadas para Win32. Cambiar únicamente la etiqueta del artefacto no constituye soporte x86.

La aplicación no requiere escribir en `Program Files` durante la operación normal; los datos de trabajo se almacenan en las carpetas del usuario.

## CLI y GUI

La CLI es el contrato de automatización y conserva sus comandos, flags y restricciones. La GUI ofrece controles para los casos de uso interactivos, incluidos procesamiento, recuperación, deduplicación, diagnóstico, preparación de Whisper, instalación del modelo local y activación opcional de WebM/TTS.

La documentación de CLI debe conservar el detalle semántico de cada opción: finalidad, valores, valores predeterminados, restricciones, incompatibilidades y efectos. Los términos técnicos, comandos, flags, rutas, APIs, formatos y nombres de modelos no se traducen.

## Documentación canónica

- [`ARCHITECTURE.md`](ARCHITECTURE.md)
- [`PIPELINE.md`](PIPELINE.md)
- [`INSTALLATION.md`](INSTALLATION.md)
- [`CONFIGURATION.md`](CONFIGURATION.md)
- [`CLI.md`](CLI.md)
- [`DESKTOP.md`](DESKTOP.md)
- [`PACKAGING.md`](PACKAGING.md)
- [`STORAGE.md`](STORAGE.md)
- [`SUBTITLES.md`](SUBTITLES.md)
- [`TRANSLATION.md`](TRANSLATION.md)
- [`TRANSLATION_PROVIDERS.md`](TRANSLATION_PROVIDERS.md)
- [`TTS.md`](TTS.md)
- [`RESUME.md`](RESUME.md)
- [`DEDUPLICATION.md`](DEDUPLICATION.md)
- [`SCHEDULING.md`](SCHEDULING.md)
- [`SECURITY.md`](SECURITY.md)
- [`TESTING.md`](TESTING.md)
- [`CI_CD.md`](CI_CD.md)
- [`DEVELOPMENT.md`](DEVELOPMENT.md)
- [`TROUBLESHOOTING.md`](TROUBLESHOOTING.md)
- [`RELEASES.md`](RELEASES.md)
- [`REGENERATION.md`](REGENERATION.md)
- [`LOCAL_TRANSLATION.md`](LOCAL_TRANSLATION.md)
- [`CUDA.md`](CUDA.md)
- [`UNINSTALLATION.md`](UNINSTALLATION.md)
