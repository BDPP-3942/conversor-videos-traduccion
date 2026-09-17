# Desinstalación y limpieza de recursos gestionados

## Modelo local de traducción

Para eliminar exclusivamente el modelo descargado por el proyecto:

```bash
python scripts/manage_runtime_resources.py translation-model cleanup
```

Esto elimina el directorio del modelo seleccionado, sin borrar código, vídeos, subtítulos, manifests, configuración ni credenciales.

Rutas gestionadas:

```text
tools/models/translation/madlad400-3b-ct2-int8/
tools/models/translation/opus-mt-es-en-ct2-int8/
```

Solo se elimina el directorio correspondiente al modelo que el comando gestiona en la configuración efectiva.

También puede consultarse antes:

```bash
python scripts/manage_runtime_resources.py translation-model status
```

## Bibliotecas CUDA gestionadas por el proyecto

Para eliminar exclusivamente las bibliotecas NVIDIA que el proyecto haya instalado bajo su directorio gestionado:

```bash
python scripts/manage_runtime_resources.py cuda cleanup
```

El directorio afectado es:

```text
tools/cuda/
```

No se desinstala el driver NVIDIA ni un CUDA Toolkit global.

## CUDA Toolkit global y driver NVIDIA

El proyecto no desinstala automáticamente estos componentes porque pueden ser necesarios para otras aplicaciones. Si fueron instalados globalmente, deben eliminarse desde el mecanismo oficial del sistema operativo/NVIDIA utilizado para instalarlos.

Antes de eliminar un Toolkit global conviene ejecutar:

```bash
python scripts/manage_runtime_resources.py cuda status
```

y comprobar qué runtime utiliza actualmente el proyecto.

## Entorno Python

Si además se quiere eliminar el entorno virtual completo, detener primero cualquier ejecución/scheduler y eliminar únicamente el entorno creado para este checkout (`.venv` si se utilizó el procedimiento documentado). No es necesario borrar `storage/` para retirar el modelo o las bibliotecas CUDA gestionadas.

## Importante

La limpieza de recursos es deliberada y no debe ejecutarse mientras exista una ejecución activa que pueda necesitarlos. Los archivos del proyecto y los recursos gestionados tienen rutas separadas para que su eliminación sea explícita y reversible mediante una nueva preparación cuando sea necesario.

## Release 1.8.0

La release publicada `1.8.0` mantiene esta separación entre datos del proyecto y recursos gestionados. La limpieza de modelos locales o del runtime CUDA no elimina artefactos de usuario ni modifica las releases/tags del repositorio.


## Aplicación de escritorio Windows

La instalación MSI proporciona dos mecanismos equivalentes para iniciar la desinstalación:

- la entrada de Aplicaciones instaladas de Windows;
- `uninstall.cmd` dentro de la carpeta de instalación.

El lanzador busca la instalación registrada por Windows Installer y ejecuta `msiexec /x` sobre el producto encontrado. No crea una clave propia en el Registro.

La desinstalación elimina los archivos instalados por el MSI y el acceso directo, pero conserva los datos privados del usuario y los recursos de trabajo. Esto incluye, cuando existan, modelos descargados, credenciales/configuración de proveedores, logs, vídeos de entrada y resultados.

La eliminación de datos de usuario debe hacerse mediante una acción explícita posterior; nunca forma parte de la desinstalación estándar.
