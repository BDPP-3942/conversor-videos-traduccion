from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_windows_installer_does_not_add_application_registry_marker() -> None:
    wix = (ROOT / "installer" / "VideoTranslationPipeline.wxs").read_text(encoding="utf-8")
    assert "<RegistryValue" not in wix
    assert 'Target="[INSTALLFOLDER]VideoTranslationPipeline.exe"' in wix


def test_windows_installer_contains_uninstall_launcher() -> None:
    launcher = (ROOT / "installer" / "uninstall.cmd").read_text(encoding="utf-8")
    assert "msiexec.exe" in launcher
    assert "/x" in launcher
    assert "Video Translation Pipeline" in launcher
