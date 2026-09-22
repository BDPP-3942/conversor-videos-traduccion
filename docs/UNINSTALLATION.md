# Desinstalación

La desinstalación elimina únicamente los archivos propios de la aplicación. No elimina automáticamente vídeos originales, resultados, modelos descargados, configuración, credenciales ni otros datos del usuario.

## Windows

Los instaladores MSI incluyen `Uninstall-VideoTranslationPipeline.ps1` dentro de la carpeta de instalación. El script localiza la instalación MSI registrada y solicita a Windows Installer la desinstalación.

Ejecuta el script con PowerShell desde la carpeta de instalación. Funciona en Windows x86, x64 y ARM64 siempre que la instalación MSI correspondiente esté registrada.

## macOS

La aplicación incluye `uninstall.sh` dentro de `VideoTranslationPipeline.app/Contents/Resources/`.

Desde Terminal:

```bash
cd "/ruta/a/VideoTranslationPipeline.app/Contents/Resources"
./uninstall.sh
```

El script elimina el bundle de la aplicación, pero no sus datos de usuario externos.

## Linux

El AppImage es un formato portátil y no instala archivos en un directorio del sistema. La aplicación contiene `uninstall.sh` en el directorio de la aplicación cuando el AppImage se extrae.

Para una instalación extraída:

```bash
cd "/ruta/a/VideoTranslationPipeline"
./uninstall.sh
```

Cuando se ejecuta desde un AppImage montado, el script puede utilizar la variable `APPIMAGE` para eliminar el propio archivo AppImage. No elimina datos de usuario.

## Seguridad y datos de usuario

El desinstalador no debe ejecutarse como administrador salvo que la propia plataforma lo requiera. Los directorios de datos de usuario permanecen intactos para evitar pérdida accidental de trabajo.
