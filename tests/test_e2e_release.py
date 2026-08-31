from __future__ import annotations

import json
import os
import pty
import shutil
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
    output = bytearray()
    previous = os.environ.copy()
    os.environ.clear()
    os.environ.update(env)

    def _read(fd: int) -> bytes:
        chunk = os.read(fd, 4096)
        output.extend(chunk)
        return chunk

    try:
        status = pty.spawn(argv, _read)
    finally:
        os.environ.clear()
        os.environ.update(previous)
    return _ProcessResult(os.waitstatus_to_exitcode(status), output.decode(errors="replace"))


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
    env["PYTHONPATH"] = os.pathsep.join(
        [str(ROOT / "tests" / "e2e_support"), str(ROOT), env.get("PYTHONPATH", "")]
    )
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


def _json_output(result: _ProcessResult) -> dict:
    starts = [
        index
        for index, char in enumerate(result.stdout)
        if char == "{" and (index == 0 or result.stdout[index - 1] == "\n")
    ]
    if not starts:
        raise AssertionError(f"CLI did not emit a JSON object: {result.stdout}")
    return json.loads(result.stdout[starts[-1] :])


def _make_video_zip(tmp_path: Path, name: str = "lesson.zip") -> Path:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        pytest.skip("ffmpeg is required for the local media E2E suite")
    media = tmp_path / "lesson.mp4"
    result = _spawn(
        [
            ffmpeg,
            "-y",
            "-f",
            "lavfi",
            "-i",
            "color=c=black:s=320x240:r=10:d=1",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=1000:duration=1",
            "-shortest",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            str(media),
        ],
        os.environ.copy(),
    )
    assert result.returncode == 0, result.stdout
    archive = tmp_path / name
    with zipfile.ZipFile(archive, "w") as handle:
        handle.write(media, media.name)
    return archive


def _fixture_dirs(config: Path) -> tuple[Path, Path]:
    data = config.read_text(encoding="utf-8")
    source = Path(data.split('source = "local://', 1)[1].split('"', 1)[0])
    target = Path(data.split('target = "local://', 1)[1].split('"', 1)[0])
    return source, target


def test_e2e_real_cli_dry_run_has_no_processing_side_effects(tmp_path: Path):
    config = _config(tmp_path)
    source, target = _fixture_dirs(config)

    result = _run("run", "--dry-run", config=config, storage_dir=tmp_path / "storage")

    assert result.returncode == 0, result.stdout
    assert _json_output(result)["status"] == "ready"
    assert list(source.iterdir()) == []
    assert list(target.iterdir()) == []
    for directory in ("input", "output", "archive", "state", "failures", "work"):
        path = tmp_path / "storage" / directory
        assert not [item for item in path.rglob("*") if item.is_file()]


def test_e2e_real_cli_concurrency_override_is_clamped(tmp_path: Path):
    config = _config(tmp_path)

    auto = _run(
        "run",
        "--dry-run",
        "--parallel-videos",
        "0",
        config=config,
        storage_dir=tmp_path / "storage",
    )
    excessive = _run(
        "run",
        "--dry-run",
        "--parallel-videos",
        "999",
        config=config,
        storage_dir=tmp_path / "storage",
    )

    assert auto.returncode == 0, auto.stdout
    assert excessive.returncode == 0, excessive.stdout
    auto_payload = _json_output(auto)
    excessive_payload = _json_output(excessive)
    assert auto_payload["effective_parallelism"] >= 1
    assert excessive_payload["effective_parallelism"] == auto_payload["effective_parallelism"]
    assert excessive_payload["effective_parallelism"] < 999


def test_e2e_real_cli_scheduled_mode_uses_same_entry_point(tmp_path: Path):
    config = _config(tmp_path)
    result = _run(
        "run",
        "--scheduled",
        "--dry-run",
        config=config,
        storage_dir=tmp_path / "storage",
    )

    assert result.returncode == 0, result.stdout
    assert _json_output(result)["status"] == "ready"


def test_e2e_real_pipeline_and_regeneration_success(tmp_path: Path):
    config = _config(tmp_path)
    source, target = _fixture_dirs(config)
    archive = _make_video_zip(tmp_path)
    shutil.copy2(archive, source / archive.name)

    first = _run(
        "run",
        "--no-retain-sources",
        config=config,
        storage_dir=tmp_path / "storage",
    )
    assert first.returncode == 0, first.stdout
    assert _json_output(first)["status"] == "success"
    outputs = [path for folder in target.iterdir() if folder.is_dir() for path in folder.glob("*.mp4")]
    assert len(outputs) == 1
    output = outputs[0]
    old_mtime = output.stat().st_mtime_ns

    regenerated = _run_regeneration(config, tmp_path / "storage")

    assert regenerated.returncode == 0, regenerated.stdout
    payload = _json_output(regenerated)
    assert payload["status"] == "success"
    assert output.is_file()
    assert output.stat().st_size > 0
    assert output.stat().st_mtime_ns >= old_mtime
    assert not list(target.glob(".regeneration-backup-*"))
    assert (source / archive.name).is_file()


def test_e2e_real_regeneration_failure_rolls_back_previous_output(tmp_path: Path):
    config = _config(tmp_path)
    source, target = _fixture_dirs(config)
    archive = _make_video_zip(tmp_path, "rollback.zip")
    shutil.copy2(archive, source / archive.name)

    first = _run(
        "run",
        "--no-retain-sources",
        config=config,
        storage_dir=tmp_path / "storage",
    )
    assert first.returncode == 0, first.stdout
    outputs = [path for folder in target.iterdir() if folder.is_dir() for path in folder.glob("*.mp4")]
    assert len(outputs) == 1
    output = outputs[0]
    old_bytes = output.read_bytes()

    (source / archive.name).write_bytes(b"not a zip")
    failed = _run_regeneration(config, tmp_path / "storage")

    assert failed.returncode != 0
    assert output.is_file()
    assert output.read_bytes() == old_bytes
    assert not list(target.glob(".regeneration-backup-*"))
    assert (source / archive.name).is_file()


def test_e2e_real_packaged_entry_points_help():
    entry_points = [
        "video-translation-pipeline",
        "video-translation-tts",
        "video-translation-regenerate",
        "video-subtitle-qa",
    ]
    for executable in entry_points:
        path = shutil.which(executable)
        if not path:
            pytest.fail(f"{executable} entry point is not installed")
        result = _spawn([path, "--help"], os.environ.copy())
        assert result.returncode == 0, executable + ": " + result.stdout
