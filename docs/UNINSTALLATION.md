# Desinstalación y limpieza de recursos gestionados

## Modelo local de traducción

Para eliminar exclusivamente el modelo descargado por el proyecto:

```bash
python scripts/manage_runtime_resources.py translation-model cleanup
```

Esto elimina:

```text
tools/models/translation/opus-mt-es-en-ct2-int8/
```

No elimina código, vídeos, subtítulos, manifests, configuración ni credenciales.

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
