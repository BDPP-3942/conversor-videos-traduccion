from pathlib import Path

import pytest

from src.file_naming import FileNameFormatter


REFERENCE_CASES = [
    ("wetransfer_1-el-juego-4-poderes-la-genesis-wmv_2026-07-21_1515.zip", "1-el juego 4 poderes la genesis.wmv", "1_el_juego_4_poderes_la_genesisx1_el_juego_4_poderes_la_genesis"),
    ("wetransfer_1-el-juego-4-poderes-la-genesis-wmv_2026-07-21_1515.zip", "2-el juego LOS 4 PODEROS alto bajo.wmv", "1_el_juego_4_poderes_la_genesisx2_el_juego_LOS_4_PODEROS_alto_bajo"),
    ("wetransfer_1-el-juego-4-poderes-la-genesis-wmv_2026-07-21_1515.zip", "4-juego 4 poderes poder de compresión.wmv", "1_el_juego_4_poderes_la_genesisx4_juego_4_poderes_poder_de_compresión"),
    ("wetransfer_estas-son-promocinales-son-6_2026-07-28_1039.zip", "COMPRENDIENDO EL PEQUEÑO TAICHI 1 (An).mp4", "estas_son_promocinales_son_6xCOMPRENDIENDO_EL_PEQUEÑO_TAICHI_1_An"),
    ("wetransfer_estas-son-promocinales-son-6_2026-07-28_1039.zip", "ESTILO LIBRE (lan Que Wei) improvisación de ejemplos.mp4", "estas_son_promocinales_son_6xESTILO_LIBRE_lan_Que_Wei_improvisación_de_ejemplos"),
    ("wetransfer_estas-son-promocinales-son-6_2026-07-28_1039.zip", "LAS 8 POSICIONES BÁSICAS DEL TAICHI.mp4", "estas_son_promocinales_son_6xLAS_8_POSICIONES_BÁSICAS_DEL_TAICHI"),
    ("wetransfer_estas-son-promocinales-son-6_2026-07-28_1039.zip", "TAICHI CHINNA (Cuello de dragón)2º parte.mp4", "estas_son_promocinales_son_6xTAICHI_CHINNA_Cuello_de_dragón_2_parte"),
    ("wetransfer_curso19-basic_2026-07-19_0916.zip", "5.-posturas fijas del taichi desde 0.mp4", "19x5_posturas_fijas_del_taichi_desde_0"),
    ("wetransfer_curso35_2026-07-19_1416.zip", "17.mp4", "35x17"),
]


@pytest.mark.parametrize("archive,filename,expected", REFERENCE_CASES)
def test_reference_tree_names_are_reproduced(archive: str, filename: str, expected: str) -> None:
    root = Path("extract")
    source = root / Path(archive).stem / filename
    metadata = FileNameFormatter.resolve_source_metadata(source, root)
    assert metadata.output_stem == expected


def test_reference_naming_is_nfc_stable_for_decomposed_source() -> None:
    root = Path("extract")
    composed = root / "wetransfer_cafe.zip" / "1-CAFÉ Niño.mp4"
    decomposed = root / "wetransfer_cafe.zip" / "1-CAFE\u0301 Nin\u0303o.mp4"

    composed_metadata = FileNameFormatter.resolve_source_metadata(composed, root)
    decomposed_metadata = FileNameFormatter.resolve_source_metadata(decomposed, root)

    assert composed_metadata.output_stem == decomposed_metadata.output_stem
