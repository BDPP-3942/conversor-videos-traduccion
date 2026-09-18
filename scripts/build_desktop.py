from __future__ import annotations

import argparse
import platform
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
APP_NAME = "VideoTranslationPipeline"


def _run(command: list[str]) -> int:
    """Ejecuta una herramienta de empaquetado desde la raíz del proyecto."""
    return subprocess.run(command, cwd=ROOT, check=False).returncode


def _windows_python_architecture() -> str:
    """Devuelve la arquitectura del intérprete Python que genera el ejecutable."""
    if sys.maxsize <= 2**32:
        return "x86"
    machine = platform.machine().lower()
    return "arm64" if machine in {"arm64", "aarch64"} else "x64"


def _build_pyinstaller() -> int:
    """Construye la aplicación de escritorio con el intérprete Python activo."""
    return _run(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            "--noconfirm",
            "--clean",
            "desktop.spec",
        ]
    )


def _build_msi(version: str, windows_arch: str) -> int:
    """Genera el MSI y comprueba que coincide con la arquitectura de Python."""
    wix = shutil.which("wix")
    if wix is None:
        print("Se necesita WiX v6 para construir el MSI de Windows.", file=sys.stderr)
        return 2
    if platform.system() != "Windows":
        print(
            "El MSI de Windows debe construirse en Windows para conservar la arquitectura correcta.",
            file=sys.stderr,
        )
        return 2
    actual_arch = _windows_python_architecture()
    if actual_arch != windows_arch:
        print(
            f"No se puede construir un MSI {windows_arch} con un intérprete Python {actual_arch}. "
            "Utiliza Python de la arquitectura correspondiente.",
            file=sys.stderr,
        )
        return 2

    source_dir = DIST / APP_NAME
    output = DIST / f"{APP_NAME}-{version}-windows-{windows_arch}.msi"
    command = [
        wix,
        "build",
        str(ROOT / "installer" / "VideoTranslationPipeline.wxs"),
        "-arch",
        windows_arch,
        "-d",
        f"Version={version}",
        "-d",
        f"SourceDir={source_dir}",
        "-o",
        str(output),
    ]
    return _run(command)


def _build_appimage(version: str, linux_arch: str | None = None) -> int:
    """Construye el AppImage Linux a partir del directorio generado por PyInstaller."""
    appimagetool = shutil.which("appimagetool")
    if appimagetool is None:
        print("Se necesita appimagetool para construir el AppImage de Linux.", file=sys.stderr)
        return 2
    app_dir = DIST / f"{APP_NAME}.AppDir"
    if app_dir.exists():
        shutil.rmtree(app_dir)
    usr_bin = app_dir / "usr" / "bin"
    usr_bin.mkdir(parents=True)
    shutil.copytree(DIST / APP_NAME, usr_bin / APP_NAME)
    shutil.copy2(
        ROOT / "installer" / "VideoTranslationPipeline.svg",
        app_dir / "VideoTranslationPipeline.svg",
    )
    (app_dir / "AppRun").write_text(
        '#!/bin/sh\nexec "$(dirname "$0")/usr/bin/VideoTranslationPipeline/VideoTranslationPipeline" "$@"\n',
        encoding="utf-8",
    )
    (app_dir / "AppRun").chmod(0o755)
    (app_dir / "VideoTranslationPipeline.desktop").write_text(
        "[Desktop Entry]\nType=Application\nName=Video Translation Pipeline\nExec=VideoTranslationPipeline"
        "\nIcon=VideoTranslationPipeline\nTerminal=false\nCategories=AudioVideo;\n",
        encoding="utf-8",
    )
    (app_dir / "VideoTranslationPipeline.desktop").chmod(0o644)
    architecture = linux_arch or platform.machine().lower()
    architecture = {"amd64": "x86_64", "x86_64": "x86_64", "aarch64": "aarch64", "arm64": "aarch64", "armv7l": "armhf", "armv7": "armhf"}.get(architecture, architecture)
    if architecture not in {"x86_64", "aarch64", "armhf"}:
        print(f"Arquitectura Linux no soportada para AppImage: {architecture}", file=sys.stderr)
        return 2
    output = DIST / f"{APP_NAME}-{version}-linux-{architecture}.AppImage"
    return _run([appimagetool, str(app_dir), str(output)])


def main() -> int:
    """Expone el CLI de construcción para los formatos de escritorio soportados."""
    parser = argparse.ArgumentParser(
        description="Construye los artefactos nativos de escritorio de Video Translation Pipeline"
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Elimina las carpetas build y dist anteriores",
    )
    parser.add_argument(
        "--format",
        choices=["native", "windows-msi", "linux-appimage"],
        default="native",
        help="Formato: native, windows-msi o linux-appimage",
    )
    parser.add_argument(
        "--version",
        required=True,
        help="Versión de release utilizada en los nombres de artefacto",
    )
    parser.add_argument(
        "--linux-arch",
        choices=["x86_64", "aarch64", "armhf"],
        default=None,
        help="Arquitectura Linux nativa para AppImage; debe coincidir con el runner.",
    )
    parser.add_argument(
        "--windows-arch",
        choices=["x64", "x86"],
        default=None,
        help="Arquitectura del MSI de Windows; por defecto se utiliza la arquitectura de Python",
    )
    args = parser.parse_args()
    if args.clean:
        for path in (ROOT / "build", DIST):
            shutil.rmtree(path, ignore_errors=True)
    result = _build_pyinstaller()
    if result != 0:
        return result
    if args.format == "windows-msi":
        uninstall_script = ROOT / "installer" / "Uninstall-VideoTranslationPipeline.ps1"
        if uninstall_script.is_file() and (DIST / APP_NAME).is_dir():
            shutil.copy2(uninstall_script, DIST / APP_NAME / uninstall_script.name)
        windows_arch = args.windows_arch or _windows_python_architecture()
        return _build_msi(args.version, windows_arch)
    if args.format == "linux-appimage":
        return _build_appimage(args.version, args.linux_arch)
    print(f"Artefacto de escritorio creado en {DIST}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
