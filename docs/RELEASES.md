# Histórico de releases

Este documento es la referencia humana del versionado del proyecto. Las releases de GitHub y sus tags son la referencia del código publicado.

## Política de versionado

Se utiliza Semantic Versioning (`MAJOR.MINOR.PATCH`):

- **MAJOR**: cambios incompatibles con configuración, CLI, formatos o contratos públicos.
- **MINOR**: funcionalidad nueva compatible hacia atrás.
- **PATCH**: correcciones compatibles, seguridad, documentación y mantenimiento.

La versión del proyecto no debe incrementarse por cada commit de formato o CI. Una release agrupa un conjunto funcional coherente.

## Funcionalidades con evidencia de introducción

| Funcionalidad | Primera versión verificada |
|---|---:|
| Pipeline audiovisual, STT, VTT, traducción, almacenamiento, resume/idempotencia, deduplicación, TTS sincronizado, ejecución programada y packaging | `1.0.0` |
| Recuperación/reparación de VTT e integración TTS en el pipeline común | `1.1.0` |
| Naming descriptivo/más resistente a colisiones y bootstrap de assets TTS | `1.2.0` |
| Corrección de instalación de assets TTS en Windows y consistencia multiplataforma | `1.2.1` |
| Limpieza de timestamps técnicos en naming | `1.2.2` |
| Concurrencia de vídeo adaptada a recursos (CPU/RAM/GPU) | `1.3.0` |
| Regeneración limpia explícita de resultados existentes | `1.4.0` |
| Integración de la regeneración existente en los wrappers locales | `1.4.1` |
| Wrappers multiplataforma con forwarding exacto, naming de referencia y contexto externo de Whisper | `1.5.0` |
| Endurecimiento de extracción ZIP y componentes de filesystem | `1.5.1` |
| Traducción local CTranslate2, recursos reproducibles y runtime Whisper controlado | `1.5.2` |

## Releases publicadas

### 1.5.0 — Multiplatform Whisper, Context & Packaging

**Tipo:** `MINOR`.

**Commit/tag publicado:** `261f4b475f452b98880815f722aa8f8f43d28097` / `v1.5.0`.

- Dispatcher común para wrappers.
- Naming basado en referencia.
- Contexto externo de Whisper.
- CI multiplataforma y packaging.

## Candidata 1.5.1 — PR1 ZIP / Unicode / Filesystem

**Tipo:** `PATCH`.

**Estado:** PR #34 fue integrada en `main` mediante el merge commit `7705987c90c6ff0b63b549c9083e43c9a6d56108`. La validación de release no debe cerrarse todavía porque la auditoría posterior detectó que el límite de naming físico debía aplicarse también de forma centralizada a los artefactos generados; esa corrección está en la PR #36.

**Alcance:**

- extracción ZIP segura frente a traversal, rutas absolutas/UNC y symlinks;
- nombres reservados de Windows;
- colisiones por case/Unicode y entradas duplicadas;
- aplicación de la política física de naming a carpetas y artefactos generados en PR #36;
- preservación separada del nombre lógico y físico;
- documentación y regresiones.

**Release gate:** el tag `v1.5.1` no debe crearse hasta que PR #36 esté integrada y el SHA final tenga CI, tests, seguridad, packaging y documentación completos.

## Candidata 1.5.2 — PR2 CUDA / Whisper / Local Translation

**Tipo:** `PATCH`.

**Estado:** PR #35 abierta. No publicada.

**Dependencia:** debe integrarse después de la release 1.5.1 y utilizar esa versión como baseline. PR #35 no debe mezclarse con ZIP/naming.

**Alcance implementado en la candidata:**

- control explícito de versiones de `faster-whisper` y CTranslate2;
- detección NVIDIA basada en `nvidia-smi` + capacidad real de CTranslate2;
- CPU como fallback de primera clase;
- AMD/ROCm detectado sin fingir compatibilidad CUDA no verificada;
- provider local `es→en` con CTranslate2 + SentencePiece;
- modelo convertido OPUS-MT fijado a revisión inmutable;
- descarga HTTPS, confirmación previa, límite de tamaño, temporales, atomicidad, `.part` y verificación SHA-256;
- recursos bajo `tools/models/translation/`;
- cleanup explícito del recurso gestionado;
- Ollama y LM Studio opcionales/no requeridos;
- fallback configurable;
- batching y reutilización del modelo;
- tests aislados de Internet/GPU/modelos reales;
- documentación de instalación, STT, translation y packaging.

**Estado de validación:** CI, packaging real, integración con un modelo descargado y benchmark CPU/GPU sobre el SHA final permanecen `NO VERIFICADO` hasta ejecutar esas validaciones.

## Política de tags

Los tags de release utilizan el formato `vMAJOR.MINOR.PATCH` y no deben reutilizarse ni moverse después de publicar una release.

`v1.5.0` permanece asociado a `261f4b475f452b98880815f722aa8f8f43d28097` y no debe modificarse.

## Historial anterior

Antes de establecer la línea de producto `1.x`, el repositorio utilizó versiones internas `4.x` y `5.x`. No se reinterpretan retroactivamente como versiones `1.x`.
