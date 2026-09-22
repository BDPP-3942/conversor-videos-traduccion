# Matriz de variantes de plataforma

Esta matriz distingue capacidad implementada, validación CI y publicación. No se considera soporte demostrado únicamente porque Python pueda arrancar.

| Variante | Runtime | STT | TTS | Packaging | CI nativa | Estado |
|---|---|---|---|---|---|---|
| Windows x86 | Python 32-bit | Vosk | SAPI/pyttsx3 | MSI | Sí | IMPLEMENTED + PACKAGED; E2E TTS físico pendiente |
| Windows x64 | Python x64 | faster-whisper/CTranslate2 | Kokoro ONNX | MSI | Sí | IMPLEMENTED + PACKAGED |
| Windows ARM64 | Python ARM64 | faster-whisper/CTranslate2, sujeto a wheels | proveedor compatible, sujeto a runtime | MSI | Sí | BUILD/CHECK en CI; E2E pendiente |
| macOS Intel | Python x64 | faster-whisper/CTranslate2 | Kokoro ONNX | .app | Sí | IMPLEMENTED + PACKAGED |
| macOS ARM64 | Python ARM64 | faster-whisper/CTranslate2, sujeto a wheels | Kokoro ONNX, sujeto a runtime | .app | Sí | BUILD/CHECK en CI; E2E pendiente |
| Linux x86 | Python x86 | backend compatible requerido | backend compatible requerido | AppImage/otro | No runner hospedado dedicado | UNVERIFIED |
| Linux x64 | Python x64 | faster-whisper/CTranslate2 | Kokoro ONNX | AppImage | Sí | IMPLEMENTED + PACKAGED |
| Linux ARM32 | Python ARM32 | backend compatible requerido | backend compatible requerido | AppImage/otro | No runner hospedado estándar | UNVERIFIED |
| Linux ARM64 | Python ARM64 | faster-whisper/CTranslate2, sujeto a wheels | Kokoro ONNX, sujeto a runtime | AppImage | Sí | BUILD/CHECK en CI; E2E pendiente |

## Reglas

- UNVERIFIED no significa PASS.
- Una build correcta no demuestra paridad funcional.
- Las variantes que sustituyen STT/TTS deben conservar un contrato funcional documentado y tests específicos.
- Linux ARM32 y Linux x86 requieren runner nativo o una estrategia de validación reproducible antes de declararse publicables.
- Windows/macOS/Linux ARM64 disponen actualmente de runners hospedados por GitHub y el workflow los utiliza para builds nativas.
- Las wheels internas no son artefactos de release por defecto.

## Validación mínima

Cada variante publicable debe comprobar: intérprete y ABI; imports y uv pip check; CLI; GUI; entrada; STT; traducción; TTS cuando esté habilitado; FFmpeg; resultado; instalación; desinstalación y limpieza.

Si una etapa no puede ejecutarse en CI debe aparecer como UNVERIFIED — LIMITACIÓN DEL ENTORNO, nunca como PASS.
