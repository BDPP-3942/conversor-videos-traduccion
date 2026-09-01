from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.skipif(os.name == "nt", reason="POSIX shell wrapper is not executable on Windows")
def test_run_local_regeneration_dispatches_to_existing_module():
    import pty

    script = ROOT / "scripts" / "run_local.sh"
    venv = ROOT / ".venv"
    python_link = venv / "bin" / "python"
    output = bytearray()
    created = False
    try:
        if not python_link.exists():
            python_link.parent.mkdir(parents=True, exist_ok=True)
            python_link.symlink_to(Path(sys.executable))
            created = True

        def read(fd: int) -> bytes:
            chunk = os.read(fd, 4096)
            output.extend(chunk)
            return chunk

        status = pty.spawn([str(script), "regenerate", "--help"], read)
        assert os.waitstatus_to_exitcode(status) == 0
        assert b"REGENERATE FROM ZERO" in output
    finally:
        if created:
            python_link.unlink(missing_ok=True)
            try:
                python_link.parent.rmdir()
                venv.rmdir()
            except OSError:
                pass
