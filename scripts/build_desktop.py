from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the Video Translation Pipeline desktop application")
    parser.add_argument("--clean", action="store_true", help="Remove the previous PyInstaller build first")
    args = parser.parse_args()
    if args.clean:
        import shutil

        for path in (ROOT / "build", ROOT / "dist"):
            shutil.rmtree(path, ignore_errors=True)
    command = [sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "desktop.spec"]
    return subprocess.run(command, cwd=ROOT, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
