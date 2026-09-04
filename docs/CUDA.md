# CUDA / NVIDIA runtime

## Objetivo

Cuando el perfil de Whisper está en `auto`, el proyecto no considera suficiente detectar una GPU NVIDIA. Debe existir un driver funcional y un runtime CUDA compatible con la versión fijada de `faster-whisper`/CTranslate2.

La versión actual del proyecto fija `faster-whisper` en `>=1.2.1,<1.3` y CTranslate2 en `>=4.8.2,<4.9`. La generación actual de faster-whisper requiere cuBLAS para CUDA 12 y cuDNN 9 para CUDA 12. CTranslate2 4.8.2 documenta soporte GPU mediante CUDA 12.x en sus ruedas Linux/Windows.

## Qué comprueba el proyecto

Antes de inicializar Whisper con `auto` o `cuda`:

1. Detecta `nvidia-smi` y obtiene GPU, driver y versión máxima CUDA anunciada por el driver.
2. Busca un CUDA Toolkit mediante `nvcc`, `CUDA_PATH` o `CUDA_HOME`.
3. Comprueba las bibliotecas cuBLAS/cuDNN del sistema y las dependencias NVIDIA gestionadas por el proyecto.
4. Identifica las versiones instaladas de `faster-whisper` y CTranslate2.
5. Ejecuta la comprobación real de capacidad de CTranslate2 (`get_cuda_device_count` y `get_supported_compute_types`).
6. Solo entonces selecciona CUDA.

Un CUDA Toolkit completo no es obligatorio para el runtime de inferencia. Si existe un Toolkit antiguo, no se sustituye automáticamente: el proyecto puede utilizar sus propias bibliotecas runtime gestionadas para evitar modificar una instalación global.

## Instalación gestionada

Si hay una NVIDIA GPU pero faltan las bibliotecas necesarias, una ejecución interactiva muestra:

- motivo del diagnóstico;
- CUDA requerido: 12.x;
- cuBLAS requerido para CUDA 12;
- cuDNN 9 para CUDA 12;
- ubicación de instalación: `tools/cuda/python/`;
- advertencia de que no se sustituye el driver ni se instala el Toolkit completo;
- confirmación explícita antes de modificar el entorno.

Las dependencias gestionadas son paquetes Python de NVIDIA y coinciden con las restricciones de `src/cuda_runtime.py`:

```text
nvidia-cublas-cu12>=12,<13
nvidia-cudnn-cu12>=9,<10
```

Las bibliotecas se anteponen al proceso mediante `PATH` en Windows y `LD_LIBRARY_PATH` en Linux. La comprobación posterior vuelve a validar CTranslate2; una instalación que no produzca capacidad CUDA utilizable no se considera correcta.

En ejecución desatendida no se solicita entrada: si el runtime no está preparado, Whisper conserva el fallback CPU en lugar de instalar software sin autorización.

## Comandos de diagnóstico y limpieza

```bash
python scripts/manage_runtime_resources.py cuda status
python scripts/manage_runtime_resources.py cuda cleanup
```

`cuda cleanup` elimina solo `tools/cuda/`, que es el directorio gestionado por el proyecto. No desinstala el driver NVIDIA ni elimina un CUDA Toolkit instalado globalmente por el usuario.

Para comprobar el modelo local:

```bash
python scripts/manage_runtime_resources.py translation-model status
python scripts/manage_runtime_resources.py translation-model cleanup
```

La limpieza del modelo elimina únicamente `tools/models/translation/opus-mt-es-en-ct2-int8/`.

## Desinstalación global de CUDA

El proyecto no ejecuta una desinstalación automática del CUDA Toolkit ni del driver porque son componentes del sistema que pueden ser utilizados por otras aplicaciones.

Si el usuario instaló un Toolkit global y quiere eliminarlo, debe utilizar el desinstalador oficial del sistema/NVIDIA correspondiente a su instalación. La aplicación solo puede garantizar la eliminación de sus recursos gestionados mediante `manage_runtime_resources.py`.

## Compatibilidad

CTranslate2 documenta soporte GPU para NVIDIA con Compute Capability >= 3.5 y ruedas precompiladas Linux/Windows; la compatibilidad efectiva también depende del driver y de las bibliotecas CUDA/cuDNN presentes.

Si la comprobación de CTranslate2 falla, el diagnóstico conserva el motivo y Whisper vuelve a CPU. No se declara una GPU como utilizable solo porque `nvidia-smi` funcione.
