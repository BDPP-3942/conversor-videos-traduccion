from pathlib import Path

import pytest

from src.archive_naming import expected_output_stem
from src.file_naming import fit_output_stem


@pytest.mark.parametrize(
    ("archive", "source", "expected"),
    (
        (
            "wetransfer_curso19-basic_2026-07-19_0916__d140128160f88ce8__d140128160f88ce8.zip",
            "2-POST FIJAS.wmv",
            "19x2_POST_FIJAS",
        ),
        (
            "wetransfer_curso35_2026-07-19_1416__083e19a07cf5f284__083e19a07cf5f284.zip",
            "17.mp4",
            "35x17",
        ),
        (
            "wetransfer_estas-son-promocinales-son-6_2026-07-28_1039__0c10ca636f4c4fc2__0c10ca636f4c4fc1.zip",
            "CHINNA EN ( Si Zheng Tui).mov",
            "estas_son_promocinales_son_6xCHINNA_EN_Si_Zheng_Tui",
        ),
    ),
)
def test_reference_tree_logical_naming_contract(tmp_path: Path, archive: str, source: str, expected: str) -> None:
    root = tmp_path / "extracted"
    path = root / archive / source
    assert expected_output_stem(path, root) == expected


def test_reference_logical_name_is_converted_to_physical_policy(tmp_path: Path) -> None:
    logical = "37_7-opt-taich-bombeosx8_OPT TAICH_pendulos (abanicos)"
    physical = fit_output_stem(logical, tmp_path)
    assert physical == "37_7_opt_taich_bombeosx8_OPT_TAICH_pendulos_abanicos"
    assert "-" not in physical
    assert "(" not in physical
    assert ")" not in physical


def test_physical_naming_preserves_scope_separator_semantics(tmp_path: Path) -> None:
    physical = fit_output_stem("19x2-POSTURAS (FIJAS)", tmp_path)
    course, resource = physical.split("x", 1)
    assert course == "19"
    assert resource == "2_POSTURAS_FIJAS"
    assert physical.count("x") == 1
