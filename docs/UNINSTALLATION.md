# Desinstalación y conservación de recursos

## Windows

El instalador MSI incluye `Uninstall-VideoTranslationPipeline.ps1` dentro de la carpeta de instalación. Al ejecutarlo se localiza la instalación MSI registrada y se solicita a Windows Installer la desinstalación.

La desinstalación elimina la aplicación instalada y sus archivos propios. **No elimina automáticamente los datos de usuario**, incluidos vídeos, resultados, modelos descargados, configuración, credenciales o estado privado.

La aplicación ya no crea una clave de registro propia para marcar la instalación; el registro utilizado por Windows Installer se limita a la información necesaria para administrar el MSI.

## Datos de usuario

Los datos de runtime se mantienen fuera de la carpeta de instalación:

- Windows: datos privados bajo `%LOCALAPPDATA%\\VideoTranslationPipeline`.
- macOS: `~/Library/Application Support/VideoTranslationPipeline`.
- Linux: `$XDG_DATA_HOME/VideoTranslationPipeline` o `~/.local/share/VideoTranslationPipeline`.

Los vídeos de entrada y resultados predeterminados permanecen en `Documentos/Video Translation Pipeline/input` y `Documentos/Video Translation Pipeline/output`.

Los modelos, TTS, rclone gestionado, credenciales y estado técnico pertenecen a los datos de usuario y requieren una limpieza explícita.

## Modelo local de traducción

Para eliminar exclusivamente el modelo descargado por el proyecto:

```bash
python scripts/manage_runtime_resources.py translation-model cleanup
```

Esto elimina el modelo seleccionado sin borrar vídeos, subtítulos, manifests, configuración ni credenciales.

## Bibliotecas CUDA gestionadas por el proyecto

```bash
python scripts/manage_runtime_resources.py cuda cleanup
```

Solo elimina las bibliotecas NVIDIA instaladas bajo el directorio gestionado por el proyecto. No desinstala el driver NVIDIA ni un CUDA Toolkit global.

## Limpieza completa de datos de aplicación

La eliminación de los datos privados debe ser una decisión explícita del usuario. Antes de hacerlo, conserva cualquier resultado, modelo o credencial que necesites posteriormente.

El objetivo de la desinstalación es separar siempre:

```text
APLICACIÓN INSTALADA
≠
DATOS Y RECURSOS DEL USUARIO
```
