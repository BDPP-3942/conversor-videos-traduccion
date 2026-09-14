from pathlib import Path


def test_rclone_setup_scripts_use_uv_managed_bootstrap() -> None:
    sh = Path("scripts/setup_rclone.sh").read_text(encoding="utf-8")
    bat = Path("scripts/setup_rclone.bat").read_text(encoding="utf-8")
    env_sh = Path("scripts/setup_env.sh").read_text(encoding="utf-8")
    env_bat = Path("scripts/setup_env.bat").read_text(encoding="utf-8")
    assert '"$UV_BIN" run python main.py provider bootstrap' in sh
    assert '"%UV_BIN%" run python main.py provider bootstrap' in bat
    assert "run python main.py provider bootstrap" in env_sh
    assert "run python main.py provider bootstrap" in env_bat
    assert "command -v rclone" not in env_sh
    assert "where rclone" not in env_bat


def test_setup_scripts_bootstrap_uv_locally_when_system_uv_is_absent() -> None:
    sh = Path("scripts/setup_env.sh").read_text(encoding="utf-8")
    bat = Path("scripts/setup_env.bat").read_text(encoding="utf-8")
    assert 'LOCAL_UV_DIR="$PROJECT_DIR/tools/uv"' in sh
    assert 'LOCAL_UV_BIN="$LOCAL_UV_DIR/uv"' in sh
    assert "UV_UNMANAGED_INSTALL" in sh
    assert "command -v uv" in sh
    assert 'set "LOCAL_UV_DIR=%CD%\\tools\\uv"' in bat
    assert 'set "LOCAL_UV_BIN=%LOCAL_UV_DIR%\\uv.exe"' in bat
    assert "UV_UNMANAGED_INSTALL" in bat
    assert "where uv.exe" in bat


def test_setup_scripts_keep_local_translation_install_opt_in() -> None:
    sh = Path("scripts/setup_env.sh").read_text(encoding="utf-8")
    bat = Path("scripts/setup_env.bat").read_text(encoding="utf-8")
    assert "--local-translation" in sh
    assert "--local-translation" in bat
    assert "scripts/manage_local_translation.py download" in sh
    assert "scripts\\manage_local_translation.py download" in bat
    assert "INSTALL_LOCAL_TRANSLATION=false" in sh
    assert "INSTALL_LOCAL_TRANSLATION=false" in bat


def test_rclone_is_external_not_a_python_dependency() -> None:
    pyproject = Path("pyproject.toml").read_text(encoding="utf-8")
    migration = Path("docs/UV_MIGRATION.md").read_text(encoding="utf-8")
    assert "rclone = []" in pyproject
    assert "external executable, not a Python dependency" in migration
    assert "tools/rclone/" in migration
    assert "secrets/rclone/rclone.conf" in migration
