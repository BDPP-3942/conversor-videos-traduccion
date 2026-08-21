# Versionado de esta base

Se reinicia la línea con `v4.0.0` porque cambia el contrato operativo: el proveedor activo y sus rutas pasan a ser estado persistente, la ejecución tiene modo desatendido y el ejecutable compilado usa su propia carpeta como raíz operativa.

## Ramas

```text
main
├── feature/provider-setup
├── feature/unattended-runner
├── feature/managed-rclone
├── feature/google-refresh
├── security/secrets
└── fix/*
```

## Commits

Usar Conventional Commits:

```text
feat(provider): add persistent Google profile setup
feat(rclone): bootstrap managed binary
feat(runtime): add unattended execution mode
fix(scheduler): prevent concurrent executions
security(secrets): keep OAuth material outside the package
```

## Releases

```text
v4.0.0  contrato operativo nuevo
v4.0.1  correcciones de instalación/scheduler
v4.1.0  nuevas funcionalidades compatibles
v5.0.0  cambios incompatibles
```
