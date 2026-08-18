# Media Processing Pipeline (STT + Translation)

Pipeline automatizado en Python para procesar archivos ZIP almacenados en Google Drive, extraer videos MP4, realizar Speech-to-Text (STT) en español con OpenAI Whisper (optimizado exclusivamente para CPU), traducir los textos resultantes al inglés y subir los MP4 junto con sus subtítulos traducidos (`.vtt`) a Google Drive.

## Modos de Ejecución
1. **LOCAL (Testing)**: Mantiene copias locales de los archivos extraídos y procesados en la carpeta `./storage/` para fácil verificación.
2. **PRODUCTION**: Utiliza carpetas temporales volátiles (`tempfile`) que se eliminan automáticamente tras el procesamiento, garantizando cero ocupación de disco persistente.

## Despliegue del Entorno Virtual

### En Windows
```cmd
scripts\setup_env.bat
```

### En Linux
```bash
chmod +x scripts/*.sh
./scripts/setup_env.sh
```

## Ejecución del Proyecto

### En Windows
```cmd
scripts\run.bat
```

### En Linux
```bash
./scripts/run.sh
```
