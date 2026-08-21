# Seguridad operacional

- `secrets/` nunca se versiona.
- `config/runtime.toml` nunca se versiona porque define el proveedor activo y rutas operativas.
- Google `token.json` y `credentials.json` deben tener permisos restrictivos.
- `rclone.conf` debe considerarse secreto: puede contener OAuth tokens, claves u otras credenciales según el backend.
- El ejecutable no contiene credenciales.
- La tarea programada debe utilizar una cuenta con el mínimo privilegio necesario.
- Nunca se registra en logs el contenido de `token.json`, `rclone.conf` ni los valores de credenciales.
- El binario rclone gestionado se verifica con SHA-256 antes de instalarse.
- La ejecución desatendida nunca intenta abrir un navegador; una pérdida de autorización produce `not_ready` para que el problema quede visible en scheduler/monitorización.

## Ejecución desatendida y OAuth

Google Drive y rclone no deben iniciar OAuth interactivo durante `run --scheduled`.

Google se valida silenciosamente y, si existe refresh token, se renueva el access token y se persiste el nuevo `token.json`. Si la renovación falla, el proceso debe quedar en `not_ready` y requerir intervención administrativa.

rclone mantiene los tokens de sus remotos dentro de `rclone.conf`. El pipeline realiza una operación de lectura antes de procesar; esto permite que rclone aplique su refresh OAuth normal cuando el backend lo soporte. Si el backend requiere consentimiento de nuevo, el scheduler no abre navegador y queda en `not_ready`.

El fichero `rclone.conf` y los `token.json` deben permanecer fuera de Git y con permisos restringidos. En Windows, la seguridad debe delegarse en ACLs de la cuenta de ejecución. En Linux, usar propietario del usuario de servicio y permisos `0600` para los secretos.
