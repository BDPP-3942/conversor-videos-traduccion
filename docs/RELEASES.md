# Histórico de releases

Este documento es la referencia humana del versionado del proyecto. Las releases de GitHub y sus tags son la referencia inmutable del código.

## Política de versionado

Se utiliza Semantic Versioning (`MAJOR.MINOR.PATCH`):

- **MAJOR**: cambios incompatibles con configuración, CLI, formatos o contratos públicos.
- **MINOR**: funcionalidad nueva compatible hacia atrás.
- **PATCH**: correcciones compatibles, seguridad, documentación y mantenimiento.

La versión del proyecto no debe incrementarse por cada commit de formato o CI. Una release agrupa un conjunto funcional coherente.

## Línea inicial

La línea moderna del proyecto tenía históricamente versiones internas `5.x` en el paquete Python. Para disponer de un histórico de releases público y limpio se establece `1.0.0` como primera release de producto de esta etapa. Esta decisión es una **rebase semántica del esquema de releases**, no una afirmación de que los commits históricos fueran literalmente versiones 1.x.

### 1.0.0 — Primera release funcional

**Tipo:** `MAJOR` / primera release estable.

**Commit de referencia:** `f0f02540426f24912ff8e6a45f92a008ef83861e`.

Esta versión representa el estado fusionado en `main` después de completar la evolución que llevó al pipeline actual. Incluye:

- pipeline de procesamiento audiovisual;
- FFmpeg para normalización y generación de medios;
- Whisper/faster-whisper para STT;
- VTT y traducción con proveedores configurables;
- gestión local y cloud mediante Google Drive/rclone;
- manifests y reanudación;
- deduplicación conservadora;
- ejecución programada y empaquetado;
- TTS sincronizado a partir del VTT traducido/corregido;
- conservación de silencios relevantes en la segmentación STT;
- generación de MP4 TTS y WebM TTS opcional;
- validación de artefactos;
- endurecimiento de seguridad y CI;
- tests y auditorías de dependencias.

**Principales hitos funcionales del historial que desembocan en 1.0.0:**

- `45d7fac` — separación de cues mediante silencios detectados.
- `316182e` — umbral de silencio configurable.
- `9103226` — tests de segmentación por silencio.
- `43cfee8` — conservación de silencios en timestamps.
- `85dca94` — endurecimiento de ejecución FFmpeg de TTS.
- `ad65af3` — restricción de rutas del CLI TTS.
- `f66c7a2` — tests de configuración TTS.
- `bcd71a5` — validación del entrypoint TTS y dependencias opcionales.
- `3d57011` — auditoría del pipeline y seguridad.
- `189ddd8` — documentación de timing STT/TTS.
- `f6f9fff` — conservación de duración original cuando la narración termina antes.
- `8801fa3` — corrección de nombres de salida en manifests cloud.
- `4ceacbf` — auditoría de dependencias TTS.
- `48c824a` — recuperación de campos de perfiles de recursos.
- `bbe082f` — corrección de anotación de configuración.
- `ad85f34` — formato Ruff canónico.
- `f0f0254` — merge de la funcionalidad completa en `main`.

Los commits puramente mecánicos de formato o CI se consideran parte de la preparación de la release y no nuevas funcionalidades independientes.

## Próximas versiones

A partir de `1.0.0`, cada cambio nuevo debe crear una release solo cuando exista un conjunto verificable de cambios.

Ejemplos:

```text
1.0.1  PATCH  corrección compatible / seguridad / documentación
1.1.0  MINOR  nueva funcionalidad compatible
1.2.0  MINOR  otra funcionalidad compatible
2.0.0  MAJOR  cambio incompatible
```

## Regla para asociar commits

Cada release debe documentar:

1. tag exacto;
2. commit apuntado por el tag;
3. tipo SemVer;
4. cambios funcionales;
5. correcciones relevantes;
6. cambios de seguridad;
7. cambios de documentación;
8. validaciones realizadas;
9. limitaciones conocidas.

El changelog no debe atribuir a una versión cambios que aparezcan después del commit etiquetado.

## Relación con GitHub

El tag y la release son la unidad de distribución. `main` representa desarrollo integrado; una release representa un estado concreto e inmutable del código.
