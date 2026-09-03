from pathlib import Path

import pytest

from src.path_limits import fit_component, is_windows_reserved_component, safe_filesystem_component


@pytest.mark.parametrize("name", ["CON", "con.txt", "PRN", "AUX.log", "NUL", "COM1", "LPT9"])
def test_windows_reserved_names_are_detected(name: str) -> None:
    assert is_windows_reserved_component(name)
    assert not is_windows_reserved_component(f"safe_{name}")


@pytest.mark.parametrize("name", ["CON", "PRN.txt", "AUX", "COM1"])
def test_reserved_component_is_prefixed(name: str) -> None:
    safe = safe_filesystem_component(name)
    assert safe.startswith("_")
    assert not is_windows_reserved_component(safe)


def test_fit_component_never_returns_reserved_name(tmp_path: Path) -> None:
    for name in ("CON", "PRN", "AUX", "NUL", "COM1", "LPT9"):
        result = fit_component(name, tmp_path)
        assert not is_windows_reserved_component(result)
