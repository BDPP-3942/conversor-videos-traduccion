from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _config(tmp_path: Path) -> Path:
    source = tmp_path / "input"
    target = tmp_path / "output"
    source.mkdir()
    target.mkdir()
    config = tmp_path / "app.toml"
    config.write_text(
        """
[app]
provider = "local"
source = "local://{source}"
target = "local://{target}"

[processing]
whisper_model = "medium"
whisper_device = "cpu"
whisper_compute_type = "int8"
whisper_cpu_threads = 16

[workflow]
max_parallel_videos = 0
resume_enabled = true

[runtime]
auto_tune_resources = false
""".format(source=source, target=target),
        encoding="utf-8",
    )
    return config


def _run(*args: str, config: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.pop("STORAGE_PROVIDER", None)
    env.pop("SOURCE_URI", None)
    env.pop("TARGET_URI", None)
    return subprocess.run(
        [sys.executable, "main.py", "--config", str(config), *args],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_e2e_real_cli_dry_run_has_no_side_effects(tmp_path: Path):
    config = _config(tmp_path)
    before = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))

    result = _run("run", "--dry-run", config=config)

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["status"] == "ready"
    after = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))
    assert after == before


def test_e2e_real_cli_concurrency_override_is_clamped(tmp_path: Path):
    config = _config(tmp_path)

    auto = _run("run", "--dry-run", "--parallel-videos", "0", config=config)
    excessive = _run("run", "--dry-run", "--parallel-videos", "999", config=config)

    assert auto.returncode == 0, auto.stdout + auto.stderr
    assert excessive.returncode == 0, excessive.stdout + excessive.stderr
    auto_payload = json.loads(auto.stdout)
    excessive_payload = json.loads(excessive.stdout)
    assert auto_payload["effective_parallelism"] >= 1
    assert excessive_payload["effective_parallelism"] == auto_payload["effective_parallelism"]
    assert excessive_payload["effective_parallelism"] < 999


def test_e2e_real_cli_scheduled_mode_uses_same_entry_point(tmp_path: Path):
    config = _config(tmp_path)
    result = _run("run", "--scheduled", "--dry-run", config=config)

    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout)["status"] == "ready"


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
