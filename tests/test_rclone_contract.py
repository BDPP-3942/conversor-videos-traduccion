from pathlib import Path


def test_rclone_setup_scripts_use_uv_managed_bootstrap() -> None:
    sh = Path("scripts/setup_rclone.sh").read_text(encoding="utf-8")
    bat = Path("scripts/setup_rclone.bat").read_text(encoding="utf-8")
    env_sh = Path("scripts/setup_env.sh").read_text(encoding="utf-8")
    env_bat = Path("scripts/setup_env.bat").read_text(encoding="utf-8")
    assert "uv run python main.py provider bootstrap" in sh
    assert "uv run python main.py provider bootstrap" in bat
    assert "uv run python main.py provider bootstrap" in env_sh
    assert "uv run python main.py provider bootstrap" in env_bat
    assert "command -v rclone" not in env_sh
    assert "where rclone" not in env_bat


def test_rclone_is_external_not_a_python_dependency() -> None:
    pyproject = Path("pyproject.toml").read_text(encoding="utf-8")
    migration = Path("docs/UV_MIGRATION.md").read_text(encoding="utf-8")
    assert 'rclone = []' in pyproject
    assert "external executable, not a Python dependency" in migration
    assert "tools/rclone/" in migration
    assert "secrets/rclone/rclone.conf" in migration
