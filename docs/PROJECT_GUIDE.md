# Guía completa del proyecto

## 1. Propósito

**Video Translation Pipeline** automatiza la preparación de vídeos para su localización. Su responsabilidad principal es transformar una entrada audiovisual en un conjunto verificable de resultados: medio normalizado, transcripción, subtítulos traducidos y, opcionalmente, una versión narrada mediante TTS.

El proyecto está pensado para procesamiento por lotes y ejecución desatendida. No es un editor audiovisual interactivo.

## 2. Alcance funcional

El sistema cubre cinco áreas:

1. **Ingesta**: recibe vídeos o paquetes ZIP desde almacenamiento local, Google Drive o un remoto compatible con rclone.
2. **Procesamiento audiovisual**: inspecciona, extrae y normaliza medios con FFmpeg.
3. **STT y subtítulos**: transcribe con Whisper/faster-whisper, conserva silencios relevantes y genera VTT con timestamps.
4. **Localización**: traduce los cues manteniendo sus intervalos temporales y permite reprocesarlos selectivamente.
5. **Entrega**: genera MP4/WebM, TTS sincronizado cuando está activado, valida artefactos, registra el estado y sube los resultados cuando procede.

También incluye deduplicación, manifests, reanudación, perfiles de proveedores, diagnósticos, empaquetado y ejecución programada.

## 3. Flujo completo

```text
Entrada
  ↓
Validación / extracción
  ↓
Normalización FFmpeg
  ↓
Whisper / VAD / segmentación
  ↓
VTT original
  ↓
Traducción
  ↓
VTT final
  ├──────────────→ subtítulos
  ├──────────────→ vídeo localizado normal
  └──────────────→ TTS opcional
                       ↓
                  cues individuales
                       ↓
                 audio temporizado
                       ↓
                  MP4 / WebM TTS
                       ↓
                 validación final
                       ↓
                    manifest
                       ↓
                almacenamiento destino
```

El VTT final es la fuente de verdad temporal para TTS. La traducción cambia el texto, no debe desplazar artificialmente los `start/end` recibidos del STT.

## 4. Silencios y timestamps

Los silencios largos son relevantes porque determinan cuándo termina una intervención y cuándo empieza la siguiente. El STT utiliza un umbral configurable para separar cues cuando existe un hueco de silencio significativo. El valor por defecto actual es 1500 ms.

Una pausa no debe rellenarse con el texto anterior ni absorberse en el siguiente cue por el mero hecho de que exista un hueco audiovisual. Los VTT resultantes deben conservar esos huecos.

El diagnóstico de subtítulos debe distinguir entre:

- huecos normales entre cues;
- solapamientos;
- cues excesivamente largos;
- timestamps inválidos;
- segmentos que cruzan un silencio que debería haber separado intervenciones.

## 5. Traducción

Los proveedores de traducción se abstraen mediante la configuración del pipeline. El proyecto contempla proveedor principal, fallback, reintentos, backoff, límites de concurrencia y lotes.

Una traducción parcial no debe marcarse como completa. Los fallos temporales de un proveedor deben poder reintentarse sin rehacer el STT cuando el VTT original sigue siendo válido.

## 6. TTS

TTS es opcional y está desacoplado del pipeline. La entrada es siempre el VTT traducido y corregido.

Para cada cue:

```text
start → end
   ↓
texto final
   ↓
TTS
   ↓
audio del cue
   ↓
encaje temporal dentro de start/end
```

Los silencios entre cues se conservan en el audio final. Si la locución supera el intervalo disponible, el pipeline puede aumentar la velocidad hasta `tts_max_speed`; si no es suficiente, el segmento se trata como problema de sincronización según la política configurada. No se desplazan los cues posteriores de forma arbitraria.

El proveedor TTS debe poder sustituirse sin modificar la lógica de sincronización ni el pipeline principal. La configuración controla proveedor, voz, idioma derivado de la configuración de destino, velocidad, modelo, bitrates y generación WebM.

## 7. Artefactos

Los artefactos concretos dependen de la configuración, pero el conjunto puede incluir:

- vídeo MP4 normal;
- vídeo WebM normal;
- VTT traducido/corregido;
- transcripción original;
- MP4 con TTS;
- WebM con TTS;
- manifest;
- registros de operación;
- historial de reprocesado o deduplicación.

Cada artefacto que participa en el estado de reanudación debe validarse antes de considerarse terminado.

## 8. Reanudación e idempotencia

El manifest permite distinguir entre etapas completadas y pendientes. El principio es:

```text
artefacto inexistente  → ejecutar
artefacto inválido     → regenerar
artefacto válido       → reutilizar
```

TTS puede ser opcional u obligatorio. Si es opcional, un fallo de TTS no invalida los resultados tradicionales. Si es obligatorio, el lote no se considera completo hasta disponer de los artefactos TTS requeridos.

Una interrupción durante una subida no debe provocar la eliminación local del resultado antes de confirmar la subida.

## 9. Almacenamiento

El procesamiento utiliza el mismo núcleo independientemente del backend. Los adaptadores se ocupan de descargar, listar, subir y confirmar resultados.

### Local

```text
storage/input/
storage/output/
storage/state/
```

### Google Drive

La autenticación OAuth es administrativa. El proceso desatendido reutiliza el perfil persistente y el refresh token cuando existe.

### rclone

El proyecto admite perfiles persistentes y puede utilizar su binario/configuración gestionados por la aplicación. El remoto activo se selecciona mediante la configuración de runtime.

## 10. Ejecución

Los distintos entrypoints deben converger en el mismo pipeline:

```text
CLI
 ├── run_local
 ├── ejecutable
 ├── scheduler
 └── cloud adapter
        ↓
   pipeline común
```

Los wrappers no deben duplicar reglas de negocio.

## 11. Ejecución programada

El diseño contempla Windows Task Scheduler, macOS launchd y cron cuando esté configurado. Las tareas deben establecer explícitamente el directorio de trabajo y utilizar rutas deterministas. No deben depender de un virtualenv activado, una terminal abierta o variables de una sesión interactiva.

## 12. CLI y operaciones habituales

```bash
python main.py --help
python main.py run --help
python main.py run
python main.py run --scheduled
python main.py doctor
python main.py reprocess-subtitles --all
```

Los comandos de proveedor permiten inspeccionar y cambiar perfiles sin modificar manualmente credenciales sensibles.

## 13. Duplicados

La deduplicación es una operación independiente y debe ser conservadora. La identidad de contenido utiliza SHA-256 y la decisión de eliminación considera la estabilidad del resultado y el registro del sistema. La deduplicación automática permanece desactivada por defecto salvo configuración explícita.

## 14. Seguridad

No se deben versionar credenciales, tokens, claves API ni configuraciones secretas. Las rutas recibidas por CLI deben validarse dentro de las raíces permitidas cuando la operación pueda escribir o borrar archivos. Los comandos FFmpeg se construyen como listas de argumentos y no deben pasar por un shell innecesario.

La CI ejecuta reglas de seguridad de Ruff y auditorías de dependencias. Las dependencias TTS opcionales se auditan por separado.

## 15. Calidad y pruebas

Antes de considerar un cambio terminado deben ejecutarse, como mínimo:

```bash
pytest
ruff check .
ruff format --check .
python -m compileall .
```

La CI además comprueba entrypoints, imports, packaging y dependencias. Los tests unitarios de proveedores externos deben usar mocks y no depender de Internet.

## 16. Empaquetado

Los scripts de compilación generan el ejecutable para los sistemas soportados. La aplicación resuelve su raíz operativa junto al ejecutable y mantiene configuración, almacenamiento y recursos externos separados del binario cuando corresponde.

Los modelos grandes no deben embutirse en el ejecutable sin una decisión explícita sobre tamaño, actualización y redistribución.

## 17. Limitaciones

La transcripción y traducción automáticas no garantizan precisión lingüística perfecta. La calidad de TTS depende del modelo, voz, idioma y hardware. Las integraciones cloud dependen de las credenciales y disponibilidad de sus respectivos proveedores.

La validación técnica de un artefacto confirma que es procesable y coherente; no sustituye una revisión audiovisual humana de calidad.

## 18. Mantenimiento

Para incorporar una nueva funcionalidad:

1. localizar el punto del pipeline responsable;
2. reutilizar las abstracciones existentes;
3. actualizar configuración y CLI si aplica;
4. actualizar manifest/resume;
5. añadir tests deterministas;
6. actualizar documentación;
7. ejecutar CI;
8. clasificar el cambio según Semantic Versioning;
9. registrar la release en `docs/RELEASES.md`.
