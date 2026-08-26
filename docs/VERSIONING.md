# Versionado de esta base

La reconstrucción comienza en `v5.0.0`. No se recupera el versionado anterior como continuidad técnica: `v5.0.0` representa el nuevo contrato funcional y operativo del proyecto reconstruido.

## Rama de reconstrucción

La Pull Request de reconstrucción se desarrolla sobre la rama principal y conserva el comportamiento útil de la implementación anterior como referencia funcional.

## Commits

Usar Conventional Commits:

```text
feat(provider): add persistent provider profile setup
feat(translation): add bounded provider fallback
fix(ci): repair reconstructed package discovery
fix(naming): restore filename compatibility helpers
fix(media): accept all advertised raw-video formats
fix(scheduler): prevent concurrent executions
test(translation): add fallback regression coverage
docs(reconstruction): document migration behavior
```

## Releases

```text
v5.0.0  reconstrucción funcional y nuevo contrato de ejecución
```

No incrementar la versión por cada corrección posterior. Los incrementos `5.x` deben corresponder a cambios reales del contrato o funcionalidades del proyecto.
