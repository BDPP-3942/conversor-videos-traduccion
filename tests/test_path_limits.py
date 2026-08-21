from pathlib import Path

from src.path_limits import fit_component, get_filesystem_limits, path_is_within_limit


def test_limits_are_discovered_from_host_filesystem(tmp_path: Path) -> None:
    limits = get_filesystem_limits(tmp_path)
    assert limits.max_component > 0
    assert limits.max_path is None or limits.max_path > limits.max_component


def test_component_is_shortened_only_when_filesystem_requires_it(tmp_path: Path) -> None:
    limits = get_filesystem_limits(tmp_path)
    long_name = "á" * (limits.max_component + 100)
    result = fit_component(long_name, tmp_path)
    assert len(result.encode("utf-8")) <= limits.max_component
    assert path_is_within_limit(tmp_path / result)


def test_unique_suffix_is_preserved_when_shortening(tmp_path: Path) -> None:
    limits = get_filesystem_limits(tmp_path)
    long_name = "á" * (limits.max_component + 100)
    result = fit_component(long_name, tmp_path, suffix="12345678")
    assert result.endswith("_12345678")
    assert len(result.encode("utf-8")) <= limits.max_component
