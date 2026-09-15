# Conversión de voz a texto (STT)

STT utiliza `faster-whisper` respaldado por CTranslate2. El modelo, dispositivo, tipo de cálculo, tamaño de beam, hilos de CPU, comportamiento de VAD, prompt inicial y política de recuperación ante degeneración seleccionados son configurables.

La release publicada `1.8.0` utiliza `faster-whisper>=1.2.1,<1.3` con `ctranslate2>=4.8.2,<4.9`. Refina el mecanismo existente de recuperación selectiva en lugar de sustituir la arquitectura STT.

Los valores predeterminados de `config/app.toml` incluyen selección automática de modelo/dispositivo/cálculo, tamaño de beam `5`, VAD habilitado, una duración mínima de silencio VAD de `2000` ms y un umbral independiente de división de subtítulos de `1000` ms. `.env.example` expone las sobreescrituras explícitas mediante variables de entorno.

## Prompt inicial / archivo de contexto

`processing.whisper_initial_prompt` acepta la forma original de prompt literal y también puede apuntar a un archivo de contexto.

Los formatos compatibles son:

- `.txt`
- `.md`
- `.csv` — las celdas se aplanan en un prompt separado por comas
- `.docx` — el texto de los párrafos se extrae de `word/document.xml` sin añadir una dependencia de runtime `python-docx`

La configuración del repositorio utiliza:

```toml
whisper_initial_prompt = "config/palabras_contexto.txt"
```

Los nombres convencionales `palabras_contexto.txt`, `palabras_contexto.md`, `palabras_contexto.csv` y `palabras_contexto.docx` también se descubren automáticamente cuando el valor configurado está vacío. Los archivos de contexto están limitados a 2 MiB y se rechaza XML de DOCX que contenga declaraciones DTD/entity.

Por ejemplo:

```toml
whisper_initial_prompt = "config/palabras_contexto.txt"
```

o, para un prompt literal:

```toml
whisper_initial_prompt = "Tai Chi, taijiquan, qigong"
```

## Detección y recuperación de degeneración de STT

La ruta normal de transcripción mantiene `whisper_condition_on_previous_text` según la configuración. Un segmento se considera sospechoso cuando la política de calidad detecta señales de degeneración, como repetición excesiva, ratio de compresión, baja probabilidad logarítmica media o alta probabilidad de ausencia de voz. La repetición legítima breve se protege mediante `whisper_min_repetition_words`.

Los segmentos sospechosos se recuperan selectivamente; los segmentos normales no se retranscriben. La recuperación se limita al segmento mediante `clip_timestamps`, de modo que un fallo en un intervalo no provoca que se regenere el archivo multimedia completo.

### Contrato de `clip_timestamps` de faster-whisper

La ruta de recuperación llama directamente a `WhisperModel.transcribe()`. Por tanto, su argumento `clip_timestamps` debe contener valores temporales numéricos, no diccionarios de segmentos. El proyecto pasa cada intervalo sospechoso como:

```python
clip_timestamps = [float(start), float(end)]
```

Esto es deliberadamente distinto de las API que pueden representar segmentos agrupados mediante diccionarios. Pasar diccionarios a la ruta `WhisperModel` provoca que falle una operación aritmética interna de `faster-whisper` con `TypeError: unsupported operand type(s) for *: 'dict' and 'int'`. Las pruebas de regresión verifican que la llamada de recuperación recibe marcas temporales numéricas.

### `whisper_recovery_retries`

`whisper_recovery_retries` es el número máximo de rondas de recuperación por segmento sospechoso. No es un bucle de reintentos ilimitado y es independiente del intento de transcripción inicial.

- `0`: desactiva la recuperación. Un segmento sospechoso se rechaza en lugar de reintentarse.
- `1`: realiza como máximo una ronda de recuperación.
- `N > 1`: realiza como máximo `N` rondas de recuperación.

Cada ronda de recuperación sigue esta política acotada:

1. Reintenta el intervalo sospechoso con `condition_on_previous_text=true` y el prompt inicial configurado, conservando el comportamiento de contexto normal.
2. Si ese resultado sigue siendo sospechoso o está vacío, reintenta el mismo intervalo con `condition_on_previous_text=false` **y sin el prompt inicial**. Esta es la ruta sin contexto/sin prompt destinada a evitar que un prompt de dominio grande amplifique las alucinaciones.
3. Si se obtiene un candidato saludable, la recuperación termina inmediatamente; no se ejecutan rondas posteriores.

Por tanto, una ronda de recuperación configurada puede realizar hasta dos llamadas `transcribe` al backend (conservando contexto y sin contexto/sin prompt). El valor de configuración cuenta rondas de recuperación, no llamadas individuales al backend.

`whisper_recovery_temperatures` proporciona la temperatura utilizada por cada ronda de recuperación. Si se configuran menos temperaturas que rondas, los valores se reutilizan cíclicamente. Si la lista está vacía, la recuperación utiliza `0.0`.

Todos los candidatos de las rondas ejecutadas se puntúan con la misma política de calidad STT. Se selecciona el mejor candidato, pero solo se emite si deja de ser sospechoso. Un candidato que siga siendo sospechoso después de todas las rondas configuradas se rechaza; el pipeline no acepta silenciosamente una transcripción conocida como degenerada.

Los logs de recuperación incluyen el intervalo, el número de reintentos configurado, el número de candidatos y las métricas/motivos de calidad, pero no registran el texto de la transcripción recuperada.

Ejemplo de configuración:

```toml
whisper_recovery_retries = 1
whisper_recovery_temperatures = [0.2]
```

Sobreescrituras mediante variables de entorno:

```text
WHISPER_RECOVERY_RETRIES=1
WHISPER_RECOVERY_TEMPERATURES=0.2,0.4
```

Las pruebas verifican la recuperación desactivada, el límite de reintentos, la selección de temperatura, el orden con/sin conservación de contexto, la omisión del prompt en el pase sin contexto y la terminación temprana después de obtener un candidato saludable.

El mecanismo de recuperación es una política defensiva de STT, no una garantía de que puedan corregirse todas las alucinaciones. Las afirmaciones de regresión sobre medios reales requieren un fixture multimedia representativo o una ejecución registrada; las pruebas sintéticas no constituyen un benchmark A/B.

## Hardware y ejecución GPU/CPU

La detección de hardware verifica la capacidad CUDA real de CTranslate2 en lugar de considerar suficiente la presencia de un driver GPU. El perfil efectivo registra CPU, RAM disponible, GPU/VRAM, modelo seleccionado, dispositivo y tipo de cálculo.

Cuando se selecciona CUDA, el modelo Whisper se ejecuta en la GPU. Los recursos de CPU siguen siendo utilizados por el pipeline circundante de Python/medios, pero `cpu_threads` no debe interpretarse como un mecanismo para dividir una inferencia Whisper entre CPU y GPU. Por tanto, el proyecto no afirma disponer de partición de un único modelo de inferencia entre CPU y GPU.

La estrategia de rendimiento compatible es el paralelismo entre trabajos de vídeo independientes cuando el presupuesto de recursos lo permite. Cada worker de vídeo posee su propia instancia de Whisper (`num_workers = 1` dentro de esa instancia), mientras que el límite de concurrencia del pipeline tiene en cuenta hilos de CPU, RAM disponible y memoria GPU. Esto evita duplicar trabajo o crear generación concurrente descontrolada dentro de una única instancia del modelo.

Si falla la inicialización CUDA, la aplicación realiza un único fallback controlado a CPU en lugar de reintentar repetidamente la misma inicialización GPU fallida.

## Segmentación

VAD y división de cues de subtítulos son controles deliberadamente independientes. `whisper_min_silence_duration_ms` se pasa al VAD de faster-whisper cuando VAD está habilitado y tiene `2000` ms como valor predeterminado en `config/app.toml`. `whisper_subtitle_split_silence_duration_ms` controla la agrupación de marcas temporales de palabras en cues de subtítulos y tiene `1000` ms como valor predeterminado.

El umbral de subtítulos no debe implementarse reduciendo el umbral VAD: VAD decide qué regiones de audio son voz, mientras que la división de subtítulos decide dónde la voz con marcas temporales de palabras debe convertirse en cues independientes. En la implementación actual, un intervalo **mayor que** el umbral configurado inicia un nuevo cue; un intervalo exactamente igual al umbral no lo hace.

Las marcas temporales de Whisper se utilizan para construir los cues de subtítulos. Los intervalos finales se validan antes de aceptar un VTT.

El invariante es:

```text
start < end
```

Los cues que incumplen el invariante no se propagan como subtítulos utilizables.

## Descarga anticipada del modelo

Para inicializar/descargar el modelo Whisper seleccionado automáticamente:

```bash
python main.py prefetch-whisper
```

El modelo no se incluye en el repositorio de forma predeterminada.

## Reprocesamiento

La línea base `1.7.0` introdujo los workflows de reprocesamiento/manifests y `1.7.1` corrigió el contrato selectivo del backend para `clip_timestamps`. La release publicada `1.8.0` conserva esos workflows y refina la recuperación de segmentos sospechosos y su gestión del contexto.
