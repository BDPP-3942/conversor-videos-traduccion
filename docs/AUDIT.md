# Auditoría del proyecto original

Fecha de revisión: 2026-08-21

## Hallazgos principales

### Estructura y repositorio

1. El ZIP incluía `.venv`, `build`, `dist`, `egg-info` y bytecode. No son código fuente y generan ruido, conflictos y revisiones de cambios aparentes.
2. El ZIP no incluía `.git`, por lo que no es posible recuperar el historial real ni determinar qué cambios fueron commits independientes. El `CHANGELOG.md` muestra saltos funcionales, pero no sustituye el historial Git.
3. `config/rclone.conf` estaba planteado como configuración operativa dentro de `config/`, aunque puede contener tokens. Se mueve a `secrets/rclone/rclone.conf`.

### Google OAuth

El comportamiento original ya guardaba el OAuth después de la primera autorización: `GoogleDriveStorageProvider._save_token()` escribía `credentials.to_json()` en `token.json`, y también lo reescribía tras un refresh. Por tanto, la parte “guardar automáticamente el OAuth de Google” ya estaba contemplada.

La mejora aplicada es separar perfiles y trasladar el token a `secrets/providers/google/<perfil>/token.json`, permitiendo varias cuentas sin sobreescrituras.

### rclone

El comportamiento original NO automatizaba la instalación ni la creación del remoto:

- `scripts/setup_rclone.*` comprobaba `where rclone` / `command -v rclone`.
- `RcloneStorageProvider` invocaba literalmente `rclone` desde el `PATH`.
- El proyecto esperaba un `rclone.conf` preexistente.
- No había gestión de perfiles ni selección activa desde la aplicación.

La versión nueva elimina esa dependencia manual: descarga un binario gestionado, conserva la configuración en secretos y añade comandos de bootstrap/list/use/remove/auth.

### Seguridad

Aspectos positivos ya presentes:

- comandos externos con listas de argumentos;
- sin `shell=True`;
- límites de extracción ZIP;
- prevención de path traversal;
- rechazo de symlinks dentro de ZIP;
- secretos excluidos de Git;
- refresh token de Google persistido para ejecución desatendida.

Mejoras aplicadas:

- configuración rclone fuera de `config/`;
- token Google por perfil;
- rclone ejecutado mediante ruta controlada por configuración;
- timeout en llamadas rclone;
- descarga de rclone verificada contra SHA-256 oficial;
- perfiles antiguos se conservan y solo se eliminan explícitamente;
- `runtime.toml` no se versiona.

## Conclusión

El proyecto original tenía una base funcional razonable, pero la gestión de proveedores estaba acoplada al pipeline y rclone se trataba como una instalación externa. La nueva arquitectura convierte autenticación/proveedor en una capa independiente y deja el pipeline de vídeo ajeno al detalle de OAuth.
