# Conversor de traducción de vídeos

Pipeline local y opcionalmente conectado a Google Drive/rclone para normalizar vídeo/audio, transcribir con Whisper y generar subtítulos traducidos.

## Almacenamiento local

El proyecto usa exclusivamente carpetas bajo `./storage` para el modo local:

```text
storage/
├── input/                         # ZIP pendientes de procesar
├── work/                          # SOLO temporales de una ejecución; siempre se eliminan
├── output/
│   ├── <resultado>/
│   │   ├── <resultado>.mp4
│   │   ├── <resultado>.mp3
│   │   ├── <resultado>_en.vtt
│   │   └── original_transcriptions/
│   │       └── <resultado>_original.vtt
│   └── _manifests/
├── archive/
│   └── sources/                   # copia local de los ZIP procesados correctamente
├── state/
│   └── processed.jsonl            # índice name + SHA-256 de ZIP procesados
├── failures/                      # errores por medio
└── logs/
```

### Detección de ZIP ya procesados

Cada ZIP local se identifica por:

- nombre del archivo;
- SHA-256 del contenido.

Solo una entrada con el mismo nombre y el mismo SHA-256 y estado `success` se considera ya procesada. Un ZIP con el mismo nombre pero contenido distinto vuelve a procesarse.

Cuando un ZIP termina correctamente, el original se copia a `storage/archive/sources/`, se verifica su SHA-256, se añade una entrada a `storage/state/processed.jsonl` y solo entonces se elimina de `storage/input/`.

Los estados `partial` y `error` no se registran como procesados y el ZIP permanece en `input` para poder reintentarlo.

Para no conservar los ZIP tras un procesamiento correcto:

```bash
python main.py run --no-retain-sources
```

## FFmpeg en local

No es necesario instalar FFmpeg globalmente ni modificar el `PATH` de Windows.

La resolución se hace en este orden:

1. `FFMPEG_BIN` / `ffmpeg.bin` configurado explícitamente.
2. `tools/ffmpeg/bin/ffmpeg.exe` (Windows) o `ffmpeg` (Linux/macOS).
3. Binario proporcionado por `imageio-ffmpeg`.
4. `PATH` del sistema como último recurso.

`setup_env.bat` y `setup_env.sh` instalan las dependencias y ejecutan `doctor` para verificar el entorno.

## Preparación local

Windows:

```bat
scripts\setup_env.bat
scripts\run_local.bat
```

Linux/macOS:

```bash
./scripts/setup_env.sh
./scripts/run_local.sh
```

Coloca los ZIP en `storage/input/`.

## Configuración que se administra manualmente

Copia `.env.example` a `.env` cuando necesites sobrescribir valores por entorno.

Para Google Drive se administra `secrets/google/credentials.json` y `secrets/google/token.json` mediante el flujo de autenticación correspondiente. No deben incluirse credenciales reales en Git.

Para rclone se administra `config/rclone.conf`.
