from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
APP_NAME = "VideoTranslationPipeline"


def _run(command: list[str]) -> int:
    return subprocess.run(command, cwd=ROOT, check=False).returncode


def _build_pyinstaller() -> int:
    return _run([sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "desktop.spec"])


def _build_msi(version: str) -> int:
    wix = shutil.which("wix")
    if wix is None:
        print("WiX v4 is required to build the Windows MSI (wix command not found).", file=sys.stderr)
        return 2
    source_dir = DIST / APP_NAME
    output = DIST / f"{APP_NAME}-{version}-windows-x64.msi"
    command = [
        wix,
        "build",
        str(ROOT / "installer" / "VideoTranslationPipeline.wxs"),
        f"-dVersion={version}",
        f"-dSourceDir={source_dir}",
        "-o",
        str(output),
    ]
    return _run(command)


def _build_appimage(version: str) -> int:
    appimagetool = shutil.which("appimagetool")
    if appimagetool is None:
        print("appimagetool is required to build the Linux AppImage.", file=sys.stderr)
        return 2
    app_dir = DIST / f"{APP_NAME}.AppDir"
    if app_dir.exists():
        shutil.rmtree(app_dir)
    usr_bin = app_dir / "usr" / "bin"
    usr_bin.mkdir(parents=True)
    shutil.copytree(DIST / APP_NAME, usr_bin / APP_NAME)
    shutil.copy2(ROOT / "installer" / "VideoTranslationPipeline.svg", app_dir / "VideoTranslationPipeline.svg")
    (app_dir / "AppRun").write_text(
        "#!/bin/sh\nexec \"$(dirname \"$0\")/usr/bin/VideoTranslationPipeline/VideoTranslationPipeline\" \"$@\"\n",
        encoding="utf-8",
    )
    (app_dir / "AppRun").chmod(0o755)
    (app_dir / "VideoTranslationPipeline.desktop").write_text(
        "[Desktop Entry]\nType=Application\nName=Video Translation Pipeline\nExec=VideoTranslationPipeline\nIcon=VideoTranslationPipeline\nTerminal=false\nCategories=AudioVideo;\n",
        encoding="utf-8",
    )
    (app_dir / "VideoTranslationPipeline.desktop").chmod(0o644)
    output = DIST / f"{APP_NAME}-{version}-linux-x86_64.AppImage"
    return _run([appimagetool, str(app_dir), str(output)])


def main() -> int:
    parser = argparse.ArgumentParser(description="Build native Video Translation Pipeline desktop artifacts")
    parser.add_argument("--clean", action="store_true", help="Remove previous build and distribution directories")
    parser.add_argument(
        "--format",
        choices=["native", "windows-msi", "linux-appimage"],
        default="native",
        help="native: target-native PyInstaller bundle; optional installer formats require their platform tool",
    )
    parser.add_argument("--version", required=True, help="Release version used in installer filenames")
    args = parser.parse_args()
    if args.clean:
        for path in (ROOT / "build", DIST):
            shutil.rmtree(path, ignore_errors=True)
    result = _build_pyinstaller()
    if result != 0:
        return result
    if args.format == "windows-msi":
        return _build_msi(args.version)
    if args.format == "linux-appimage":
        return _build_appimage(args.version)
    print(f"Native desktop artifact created under {DIST}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
