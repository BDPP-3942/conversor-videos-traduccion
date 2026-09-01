from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@dataclass
class _ProcessResult:
    returncode: int
    stdout: str


def _spawn(argv: list[str], env: dict[str, str]) -> _ProcessResult:
    result = subprocess.run(argv, env=env, capture_output=True, text=True, check=False)
    return _ProcessResult(result.returncode, result.stdout + result.stderr)


def _config(tmp_path: Path) -> Path:
    source = tmp_path / "input"
    target = tmp_path / "output"
    storage = tmp_path / "storage"
    source.mkdir()
    target.mkdir()
    storage.mkdir()
    config = tmp_path / "app.toml"
    config.write_text(
        """
[app]
provider = "local"
source = "local://{source}"
target = "local://{target}"

[processing]
whisper_model = "tiny"
whisper_device = "cpu"
whisper_compute_type = "int8"
whisper_cpu_threads = 16
translation_provider = "mymemory"
translation_retries = 1
translation_batch_size = 4
translation_min_request_interval_seconds = 0
translation_retry_delay_seconds = 0

[ffmpeg]
generate_webm = false
avoid_reencode = false
timeout_seconds = 60

[local]
retain_sources = true
input_min_age_seconds = 0

[workflow]
max_parallel_videos = 0
resume_enabled = true

[runtime]
auto_tune_resources = false
run_lock_file = "{lock}"
""".format(source=source, target=target, lock=storage / "run.lock"),
        encoding="utf-8",
    )
    return config


def _env(storage_dir: Path) -> dict[str, str]:
    env = os.environ.copy()
    env.pop("STORAGE_PROVIDER", None)
    env.pop("SOURCE_URI", None)
    env.pop("TARGET_URI", None)
    env["PYTHONPATH"] = os.pathsep.join([str(ROOT / "tests" / "e2e_support"), str(ROOT), env.get("PYTHONPATH", "")])
    env["E2E_STORAGE_DIR"] = str(storage_dir)
    return env


def _run(*args: str, config: Path, storage_dir: Path | None = None) -> _ProcessResult:
    env = _env(storage_dir or config.parent / "storage")
    return _spawn([sys.executable, "main.py", "--config", str(config), *args], env)


def _run_regeneration(config: Path, storage_dir: Path) -> _ProcessResult:
    executable = shutil.which("video-translation-regenerate")
    if not executable:
        pytest.fail("video-translation-regenerate entry point is not installed")
    return _spawn([executable, "--config", str(config)], _env(storage_dir))


def _run_regeneration_wrapper(config: Path, storage_dir: Path) -> _ProcessResult:
    if os.name == "nt":
        pytest.skip("POSIX wrapper E2E requires a POSIX shell")
    script = ROOT / "scripts" / "run_local.sh"
    venv = ROOT / ".venv"
    python_link = venv / "bin" / "python"
    created = False
    try:
        if not python_link.exists():
            python_link.parent.mkdir(parents=True, exist_ok=True)
            python_link.symlink_to(Path(sys.executable))
            created = True
        return _spawn([str(script), "regenerate", "--config", str(config)], _env(storage_dir))
    finally:
        if created:
            python_link.unlink(missing_ok=True)
            try:
                python_link.parent.rmdir()
                venv.rmdir()
            except OSError:
                pass


def _json_output(result: _ProcessResult) -> dict:
    starts = [
        index
        for index, char in enumerate(result.stdout)
        if char == "{" and (index == 0 or result.stdout[index - 1] == "\n")
    ]
    if not starts:
        raise AssertionError(f"CLI did not emit a JSON object: {result.stdout}")
    payload, _ = json.JSONDecoder().raw_decode(result.stdout[starts[-1] :])
    return payload


def _make_video_zip(tmp_path: Path, name: str = "lesson.zip") -> Path:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        pytest.skip("ffmpeg is required for the local media E2E suite")
    media = tmp_path / "lesson.mp4"
    result = _spawn(
        [ffmpeg, "-y", "-f", "lavfi", "-i", "color=c=black:s=320x240:d=0.2", "-an", str(media)],
        os.environ.copy(),
    )
    assert result.returncode == 0, result.stdout
    archive = tmp_path / name
    with zipfile.ZipFile(archive, "w") as handle:
        handle.write(media, media.name)
    return archive
