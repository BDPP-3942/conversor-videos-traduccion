from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_run_local_regeneration_dispatches_to_existing_module():
    if os.name == "nt":
        pytest.skip("Shell wrapper is POSIX-specific")

    script = ROOT / "scripts" / "run_local.sh"
    venv = ROOT / ".venv"
    python_link = venv / "bin" / "python"
    created = False
    try:
        if not python_link.exists():
            python_link.parent.mkdir(parents=True, exist_ok=True)
            python_link.symlink_to(Path(sys.executable))
            created = True

        completed = subprocess.run(
            [str(script), "regenerate", "--help"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert completed.returncode == 0, completed.stderr + completed.stdout
        assert "REGENERATE FROM ZERO" in completed.stdout
    finally:
        if created:
            python_link.unlink(missing_ok=True)
            try:
                python_link.parent.rmdir()
                venv.rmdir()
            except OSError:
                pass
