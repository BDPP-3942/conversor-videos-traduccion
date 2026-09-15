# Índice de documentación

Esta es la entrada principal a la documentación del proyecto. La documentación operativa debe estar en español y, cuando se cite otro documento del repositorio, debe utilizar un enlace Markdown relativo.

## Producto y arquitectura

- [`PROJECT.md`](PROJECT.md)
- [`ARCHITECTURE.md`](ARCHITECTURE.md)
- [`USE_CASES.md`](USE_CASES.md)
- [`PIPELINE.md`](PIPELINE.md)

## Uso

- [`INSTALLATION.md`](INSTALLATION.md)
- [`CONFIGURATION.md`](CONFIGURATION.md)
- [`CLI.md`](CLI.md)
- [`DESKTOP.md`](DESKTOP.md)
- [`STORAGE.md`](STORAGE.md)
- [`SCHEDULING.md`](SCHEDULING.md)

## Procesamiento

- [`STT.md`](STT.md)
- [`SUBTITLES.md`](SUBTITLES.md)
- [`TRANSLATION.md`](TRANSLATION.md)
- [`TRANSLATION_PROVIDERS.md`](TRANSLATION_PROVIDERS.md)
- [`LOCAL_TRANSLATION.md`](LOCAL_TRANSLATION.md)
- [`TTS.md`](TTS.md)
- [`RESUME.md`](RESUME.md)
- [`DEDUPLICATION.md`](DEDUPLICATION.md)
- [`REGENERATION.md`](REGENERATION.md)

## Distribución y mantenimiento

- [`PACKAGING.md`](PACKAGING.md)
- [`UNINSTALLATION.md`](UNINSTALLATION.md)
- [`TROUBLESHOOTING.md`](TROUBLESHOOTING.md)
- [`TESTING.md`](TESTING.md)
- [`CI_CD.md`](CI_CD.md)
- [`DEVELOPMENT.md`](DEVELOPMENT.md)
- [`SECURITY.md`](SECURITY.md)
- [`CUDA.md`](CUDA.md)

## Releases

- [`RELEASES.md`](RELEASES.md)
- [`VERSIONING.md`](VERSIONING.md)
- [`../CHANGELOG.md`](../CHANGELOG.md)

## Regla documental

Los documentos nuevos y las modificaciones de documentación deben redactarse en español. Los nombres técnicos de APIs, comandos, opciones CLI, variables de configuración, clases, funciones, rutas y nombres de artefactos se conservan literalmente cuando forman parte del contrato del software.

Cuando un documento mencione otro documento del repositorio, debe utilizar un enlace relativo en lugar de un nombre de archivo aislado. Los comandos de CLI deben reflejar el estado real de `--help`; si cambia el parser, debe actualizarse [`CLI.md`](CLI.md) en el mismo cambio.
