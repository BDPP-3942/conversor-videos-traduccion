from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    "script, command",
    [
        ("scripts/run_local.sh", 'exec "$UV_BIN" run python scripts/run_local.py "$@"'),
        ("scripts/setup_rclone.sh", 'exec "$UV_BIN" run python main.py provider bootstrap'),
        ("scripts/setup_google.sh", 'exec "$UV_BIN" run python main.py auth google'),
        ("scripts/build_linux.sh", '"$UV_BIN" run python -m PyInstaller'),
    ],
)
def test_posix_wrappers_use_shared_uv_resolver(script: str, command: str) -> None:
    content = (ROOT / script).read_text(encoding="utf-8")
    assert 'source "$PROJECT_DIR/scripts/lib/resolve_uv.sh"' in content
    assert 'UV_BIN="$(resolve_uv "$PROJECT_DIR")"' in content
    assert command in content
    assert "command -v uv >/dev/null 2>&1 || {" not in content


def test_posix_resolver_prefers_project_managed_uv() -> None:
    resolver = (ROOT / "scripts/lib/resolve_uv.sh").read_text(encoding="utf-8")
    assert 'local_uv="$project_dir/tools/uv/uv"' in resolver
    assert 'if [[ -x "$local_uv" ]]; then' in resolver
    assert "command -v uv" in resolver
    assert resolver.index('if [[ -x "$local_uv" ]]; then') < resolver.index("command -v uv")


def test_windows_resolver_contract_is_available_to_cmd_wrappers() -> None:
    resolver = (ROOT / "scripts/lib/resolve_uv.bat").read_text(encoding="utf-8")
    assert "tools\\uv\\uv.exe" in resolver
    assert "where uv.exe" in resolver


def test_windows_wrappers_use_shared_uv_resolver() -> None:
    for script in (
        "scripts/run_local.bat",
        "scripts/setup_rclone.bat",
        "scripts/setup_google.bat",
        "scripts/build_windows.bat",
    ):
        content = (ROOT / script).read_text(encoding="utf-8")
        assert 'call "%~dp0lib\\resolve_uv.bat"' in content
        assert '"%UV_BIN%"' in content
        assert "where uv.exe" not in content


def test_windows_unattended_uses_resolver_before_python_fallback() -> None:
    content = (ROOT / "scripts/run_unattended.bat").read_text(encoding="utf-8")
    assert content.count('call "%~dp0lib\\resolve_uv.bat"') == 2
    assert '"%UV_BIN%" run python main.py' in content
    assert "where uv.exe" not in content


def test_windows_resolver_prefers_project_managed_uv_before_path() -> None:
    resolver = (ROOT / "scripts/lib/resolve_uv.bat").read_text(encoding="utf-8")
    local_check = 'if exist "%~dp0..\\..\\tools\\uv\\uv.exe"'
    assert local_check in resolver
    assert "where uv.exe" in resolver
    assert resolver.index(local_check) < resolver.index("where uv.exe")


def test_run_unattended_preserves_packaged_executable_priority() -> None:
    for script in ("scripts/run_unattended.sh", "scripts/run_unattended.bat"):
        content = (ROOT / script).read_text(encoding="utf-8")
        assert "dist" in content
        assert "VideoTranslationPipeline" in content
