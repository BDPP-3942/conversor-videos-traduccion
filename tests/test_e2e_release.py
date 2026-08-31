from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


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


def _run(*args: str, config: Path, storage_dir: Path | None = None) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.pop("STORAGE_PROVIDER", None)
    env.pop("SOURCE_URI", None)
    env.pop("TARGET_URI", None)
    env["PYTHONPATH"] = os.pathsep.join(
        [str(ROOT / "tests" / "e2e_support"), str(ROOT), env.get("PYTHONPATH", "")]
    )
    if storage_dir:
        env["E2E_STORAGE_DIR"] = str(storage_dir)
    return subprocess.run(
        [sys.executable, "main.py", "--config", str(config), *args],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def _make_video_zip(tmp_path: Path, name: str = "lesson.zip") -> Path:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        pytest.skip("ffmpeg is required for the local media E2E suite")
    media = tmp_path / "lesson.mp4"
    subprocess.run(
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
        check=True,
        capture_output=True,
    )
    archive = tmp_path / name
    with zipfile.ZipFile(archive, "w") as handle:
        handle.write(media, media.name)
    return archive


def _fixture_dirs(config: Path) -> tuple[Path, Path]:
    data = config.read_text(encoding="utf-8")
    source = Path(data.split('source = "local://', 1)[1].split('"', 1)[0])
    target = Path(data.split('target = "local://', 1)[1].split('"', 1)[0])
    return source, target


def test_e2e_real_cli_dry_run_has_no_side_effects(tmp_path: Path):
    config = _config(tmp_path)
    before = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))

    result = _run("run", "--dry-run", config=config, storage_dir=tmp_path / "storage")

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["status"] == "ready"
    after = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))
    assert after == before


def test_e2e_real_cli_concurrency_override_is_clamped(tmp_path: Path):
    config = _config(tmp_path)

    auto = _run("run", "--dry-run", "--parallel-videos", "0", config=config, storage_dir=tmp_path / "storage")
    excessive = _run(
        "run", "--dry-run", "--parallel-videos", "999", config=config, storage_dir=tmp_path / "storage"
    )

    assert auto.returncode == 0, auto.stdout + auto.stderr
    assert excessive.returncode == 0, excessive.stdout + excessive.stderr
    auto_payload = json.loads(auto.stdout)
    excessive_payload = json.loads(excessive.stdout)
    assert auto_payload["effective_parallelism"] >= 1
    assert excessive_payload["effective_parallelism"] == auto_payload["effective_parallelism"]
    assert excessive_payload["effective_parallelism"] < 999


def test_e2e_real_cli_scheduled_mode_uses_same_entry_point(tmp_path: Path):
    config = _config(tmp_path)
    result = _run("run", "--scheduled", "--dry-run", config=config, storage_dir=tmp_path / "storage")

    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout)["status"] == "ready"


def test_e2e_real_pipeline_and_regeneration_success(tmp_path: Path):
    config = _config(tmp_path)
    source, target = _fixture_dirs(config)
    archive = _make_video_zip(tmp_path)
    shutil.copy2(archive, source / archive.name)

    first = _run("run", "--no-retain-sources", config=config, storage_dir=tmp_path / "storage")
    assert first.returncode == 0, first.stdout + first.stderr
    first_payload = json.loads(first.stdout)
    assert first_payload["status"] == "success"
    folders = [item for item in target.iterdir() if item.is_dir()]
    assert folders
    old_output = next(folder.glob("*.mp4") for folder in folders)
    old_bytes = old_output.read_bytes()

    regenerated = _run(
        "--config-does-not-exist",
        config=config,
        storage_dir=tmp_path / "storage",
    )
    assert regenerated.returncode != 0

    regenerated = subprocess.run(
        ["video-translation-regenerate", "--config", str(config)],
        cwd=ROOT,
        env={
            **os.environ,
            "PYTHONPATH": os.pathsep.join(
                [str(ROOT / "tests" / "e2e_support"), str(ROOT), os.environ.get("PYTHONPATH", "")]
            ),
            "E2E_STORAGE_DIR": str(tmp_path / "storage"),
        },
        capture_output=True,
        text=True,
        check=False,
    )
    assert regenerated.returncode == 0, regenerated.stdout + regenerated.stderr
    payload = json.loads(regenerated.stdout)
    assert payload["status"] == "success"
    assert not list(target.glob(".regeneration-backup-*"))
    assert old_output.is_file()
    assert old_output.read_bytes() != old_bytes or payload["pipeline"]["status"] == "success"
    assert (source / archive.name).is_file()


def test_e2e_real_regeneration_failure_rolls_back_previous_output(tmp_path: Path):
    config = _config(tmp_path)
    source, target = _fixture_dirs(config)
    archive = _make_video_zip(tmp_path, "rollback.zip")
    shutil.copy2(archive, source / archive.name)

    first = _run("run", "--no-retain-sources", config=config, storage_dir=tmp_path / "storage")
    assert first.returncode == 0, first.stdout + first.stderr
    folders = [item for item in target.iterdir() if item.is_dir()]
    assert folders
    old_output = next(folder.glob("*.mp4") for folder in folders)
    old_bytes = old_output.read_bytes()

    (source / archive.name).write_bytes(b"not a zip")
    failed = subprocess.run(
        ["video-translation-regenerate", "--config", str(config)],
        cwd=ROOT,
        env={
            **os.environ,
            "PYTHONPATH": os.pathsep.join(
                [str(ROOT / "tests" / "e2e_support"), str(ROOT), os.environ.get("PYTHONPATH", "")]
            ),
            "E2E_STORAGE_DIR": str(tmp_path / "storage"),
        },
        capture_output=True,
        text=True,
        check=False,
    )
    assert failed.returncode != 0
    assert old_output.is_file()
    assert old_output.read_bytes() == old_bytes
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
        result = subprocess.run(
            [executable, "--help"], cwd=ROOT, capture_output=True, text=True, check=False
        )
        assert result.returncode == 0, executable + ": " + result.stdout + result.stderr
