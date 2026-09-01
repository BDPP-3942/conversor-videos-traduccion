from pathlib import Path

import pytest
from src.file_naming import FileNameFormatter


REFERENCE_CASES = [
    ("wetransfer_1-el-juego-4-poderes-la-genesis-wmv_2026-07-21_1515__8bf4b7d4cae733d5__8bf4b7d4cae733d5.zip", "1-el juego 4 poderes la genesis.wmv", "1_el_juego_4_poderes_la_genesisx1_el_juego_4_poderes_la_genesis"),
    ("wetransfer_1-el-juego-4-poderes-la-genesis-wmv_2026-07-21_1515__8bf4b7d4cae733d5__8bf4b7d4cae733d5.zip", "2-el juego LOS 4 PODEROS alto bajo.wmv", "1_el_juego_4_poderes_la_genesisx_2_el_juego_LOS_4_PODEROS_alto_bajo"),
    ("wetransfer_1-el-juego-4-poderes-la-genesis-wmv_2026-07-21_1515__8bf4b7d4cae733d5__8bf4b7d4cae733d5.zip", "3-el ju los 4 vpoderes inflado.wmv", "1_el_juego_4_poderes_la_genesisx3_el_ju_los_4_vpoderes_inflado"),
    ("wetransfer_1-el-juego-4-poderes-la-genesis-wmv_2026-07-21_1515__8bf4b7d4cae733d5__8bf4b7d4cae733d5.zip", "4-juego 4 poderes poder de compresión.wmv", "1_el_juego_4_poderes_la_genesisx4_juego_4_poderes_poder_de_compresión"),
    ("wetransfer_1-el-juego-4-poderes-la-genesis-wmv_2026-07-21_1515__8bf4b7d4cae733d5__8bf4b7d4cae733d5.zip", "5-juego 4 poderes poder de repliegue.wmv", "1_el_juego_4_poderes_la_genesisx5_juego_4_poderes_poder_de_repliegue"),
    ("wetransfer_1-el-juego-4-poderes-la-genesis-wmv_2026-07-21_1515__8bf4b7d4cae733d5__8bf4b7d4cae733d5.zip", "6-juego 4 poders poder de empuje.wmv", "1_el_juego_4_poderes_la_genesisx6_juego_4_poders_poder_de_empuje"),
    ("wetransfer_1-el-juego-4-poderes-la-genesis-wmv_2026-07-21_1515__8bf4b7d4cae733d5__8bf4b7d4cae733d5.zip", "7- juego 4 poderes.wmv", "1_el_juego_4_poderes_la_genesisx7_juego_4_poderes"),
    ("wetransfer_1o-optimizadores-de-taichi-la-danza-del-arco-iris-mp4_2026-07-19_2215__adae04e10233151a__adae04e10233151a.zip", "1º OPTIMIZADORES DE TAICHI la danza del arco iris.mp4", "1-optimizadores-de-taichi-la-danza-del-arco-irisx1_OPTIMIZADORES_DE_TAICHI_la_danza_del_arco_iris"),
    ("wetransfer_1o-optimizadores-de-taichi-la-danza-del-arco-iris-mp4_2026-07-19_2215__adae04e10233151a__adae04e10233151a.zip", "2º opt de taich LA GRAN RUEDA.mp4", "1-optimizadores-de-taichi-la-danza-del-arco-irisx2_opt_de_taich_LA_GRAN_RUEDA"),
    ("wetransfer_1o-optimizadores-de-taichi-la-danza-del-arco-iris-mp4_2026-07-19_2215__adae04e10233151a__adae04e10233151a.zip", "3º optimizadores del tai-chi EL TAMBOR CHINO ALCANZA EL CIELO.mp4", "1-optimizadores-de-taichi-la-danza-del-arco-irisx3_optimizadores_del_tai-chi_EL_TAMBOR_CHINO_ALCANZA_EL_CIELO"),
    ("wetransfer_1o-optimizadores-de-taichi-la-danza-del-arco-iris-mp4_2026-07-19_2215__adae04e10233151a__adae04e10233151a.zip", "4º OPT TAICH arqueos de bambu.mp4", "1-optimizadores-de-taichi-la-danza-del-arco-irisx4_OPT_TAICH_arqueos_de_bambu"),
    ("wetransfer_1o-optimizadores-de-taichi-la-danza-del-arco-iris-mp4_2026-07-19_2215__adae04e10233151a__adae04e10233151a.zip", "5ºoptim taich  MANOS COMO NUBES.mp4", "1-optimizadores-de-taichi-la-danza-del-arco-irisx5_optim_taich_MANOS_COMO_NUBES"),
    ("wetransfer_1o-optimizadores-de-taichi-la-danza-del-arco-iris-mp4_2026-07-19_2215__adae04e10233151a__adae04e10233151a.zip", "6º opt taich TOCAR EL CIELO  Y ALCANZAR EL FONDO DEL MAR.mp4", "1-optimizadores-de-taichi-la-danza-del-arco-irisx6_opt_taich_TOCAR_EL_CIELO_Y_ALCANZAR_EL_FONDO_DEL_MAR"),
    ("wetransfer_6-boxeo-sombras-filo-wmv_2026-07-27_1138__89de9eb473373033__89de9eb473373033.zip", "6. BOXEO SOMBRAS filo.wmv", "6-boxeo-sombras-filox6_BOXEO_SOMBRAS_filo"),
    ("wetransfer_6-boxeo-sombras-filo-wmv_2026-07-27_1138__89de9eb473373033__89de9eb473373033.zip", "7. BOXEO SOMBRAS pica.wmv", "6-boxeo-sombras-filox7_BOXEO_SOMBRAS_pica"),
    ("wetransfer_6-boxeo-sombras-filo-wmv_2026-07-27_1138__89de9eb473373033__89de9eb473373033.zip", "8. BOXEO SOMBRAS Lomo y dorso.wmv", "6-boxeo-sombras-filox8_BOXEO_SOMBRAS_Lomo_y_dorso"),
    ("wetransfer_6-boxeo-sombras-filo-wmv_2026-07-27_1138__89de9eb473373033__89de9eb473373033.zip", "9. BOXEO SOMBRAS palma.wmv", "6-boxeo-sombras-filox9_BOXEO_SOMBRAS_palma"),
    ("wetransfer_6-boxeo-sombras-filo-wmv_2026-07-27_1138__89de9eb473373033__89de9eb473373033.zip", "10. BOXEO SOMBRAS variaciones.wmv", "6-boxeo-sombras-filox10_BOXEO_SOMBRAS_variaciones"),
    ("wetransfer_7o-opt-taich-bombeos-mp4_2026-07-20_1135__f0232f8d88590c18__f0232f8d88590c18.zip", "7º opt taich BOMBEOS.mp4", "7-opt-taich-bombeosx7_opt_taich_BOMBEOS"),
    ("wetransfer_7o-opt-taich-bombeos-mp4_2026-07-20_1135__f0232f8d88590c18__f0232f8d88590c18.zip", "8º OPT TAICH pendulos, abanicos, lanzamientos.mp4", "7-opt-taich-bombeosx8_OPT_TAICH_pendulos_abanicos_lanzamientos"),
    ("wetransfer_7o-opt-taich-bombeos-mp4_2026-07-20_1135__f0232f8d88590c18__f0232f8d88590c18.zip", "9º opt de taich LA DANZA DEL TAO.mp4", "7-opt-taich-bombeosx9_opt_de_taich_LA_DANZA_DEL_TAO"),
    ("wetransfer_7o-opt-taich-bombeos-mp4_2026-07-20_1135__f0232f8d88590c18__f0232f8d88590c18.zip", "20 peng.mp4", "7_opt_taich_bombeosx20_peng"),
    ("wetransfer_curso19-basic_2026-07-19_0916__d140128160f88ce8__d140128160f88ce8.zip", "1-POST FIJAS.wmv", "19x1_POST_FIJAS"),
    ("wetransfer_curso19-basic_2026-07-19_0916__d140128160f88ce8__d140128160f88ce8.zip", "2-POST FIJAS.wmv", "19x2_POST_FIJAS"),
    ("wetransfer_curso19-basic_2026-07-19_0916__d140128160f88ce8__d140128160f88ce8.zip", "3-POSTURAS FIJAS.wmv", "19x3_POSTURAS_FIJAS"),
    ("wetransfer_curso19-basic_2026-07-19_0916__d140128160f88ce8__d140128160f88ce8.zip", "4-POSTURAS FIJAS.wmv", "19x4_POSTURAS_FIJAS"),
    ("wetransfer_curso19-basic_2026-07-19_0916__d140128160f88ce8__d140128160f88ce8.zip", "5.-posturas fijas del taichi desde 0.mp4", "19x5_posturas_fijas_del_taichi_desde_0"),
    ("wetransfer_curso19_2026-07-19_1050__32583ebc9402d291__32583ebc9402d291.zip", "6.-CONEXIONES.mp4", "19x6_CONEXIONES"),
    ("wetransfer_curso19_2026-07-19_1050__32583ebc9402d291__32583ebc9402d291.zip", "7.-manos de seda CONEXIONES.mp4", "19x7_manos_de_seda_CONEXIONES"),
    ("wetransfer_curso19_2026-07-19_1050__32583ebc9402d291__32583ebc9402d291.zip", "8. CONEXIONES EN LA FORMA.mp4", "19x8_CONEXIONES_EN_LA_FORMA"),
    ("wetransfer_curso19_2026-07-19_1050__32583ebc9402d291__32583ebc9402d291.zip", "9.-QUIETUD AL MOV. variantes estructura y posiciones.mp4", "19x9_QUIETUD_AL_MOV_variantes_estructura_y_posiciones"),
    ("wetransfer_curso19_2026-07-19_1050__32583ebc9402d291__32583ebc9402d291.zip", "10.-de la quietud al movimiento MOVER LA ESTRUCTURA.mp4", "19x10_de_la_quietud_al_movimiento_MOVER_LA_ESTRUCTURA"),
    ("wetransfer_curso35_2026-07-19_1416__083e19a07cf5f284__083e19a07cf5f284.zip", "17.mp4", "35x17"),
    ("wetransfer_curso35_2026-07-19_1416__083e19a07cf5f284__083e19a07cf5f284.zip", "18.mp4", "35x18"),
    ("wetransfer_curso35_2026-07-19_1416__083e19a07cf5f284__083e19a07cf5f284.zip", "19.mp4", "35x19"),
    ("wetransfer_curso37_1o-optimizadores-de-taichi-la-danza-del-arco-iris-mp4_2026-07-19_2215__adae04e10233151a__adae04e10233151a.zip", "1º OPTIMIZADORES DE TAICHI la danza del arco iris.mp4", "37_1-optimizadores-de-taichi-la-danza-del-arco-irisx1_OPTIMIZADORES_DE_TAICHI_la_danza_del_arco_iris"),
    ("wetransfer_curso37_1o-optimizadores-de-taichi-la-danza-del-arco-iris-mp4_2026-07-19_2215__adae04e10233151a__adae04e10233151a.zip", "2º opt de taich LA GRAN RUEDA.mp4", "37_1-optimizadores-de-taichi-la-danza-del-arco-irisx2_opt_de_taich_LA_GRAN_RUEDA"),
    ("wetransfer_curso37_1o-optimizadores-de-taichi-la-danza-del-arco-iris-mp4_2026-07-19_2215__adae04e10233151a__adae04e10233151a.zip", "3º optimizadores del tai-chi EL TAMBOR CHINO ALCANZA EL CIELO.mp4", "37_1-optimizadores-de-taichi-la-danza-del-arco-irisx3_optimizadores_del_tai-chi_EL_TAMBOR_CHINO_ALCANZA_EL_CIELO"),
    ("wetransfer_curso37_1o-optimizadores-de-taichi-la-danza-del-arco-iris-mp4_2026-07-19_2215__adae04e10233151a__adae04e10233151a.zip", "4º OPT TAICH arqueos de bambu.mp4", "37_1-optimizadores-de-taichi-la-danza-del-arco-irisx4_OPT_TAICH_arqueos_de_bambu"),
    ("wetransfer_curso37_1o-optimizadores-de-taichi-la-danza-del-arco-iris-mp4_2026-07-19_2215__adae04e10233151a__adae04e10233151a.zip", "5ºoptim taich  MANOS COMO NUBES.mp4", "37_1-optimizadores-de-taichi-la-danza-del-arco-irisx5_optim_taich_MANOS_COMO_NUBES"),
    ("wetransfer_curso37_1o-optimizadores-de-taichi-la-danza-del-arco-iris-mp4_2026-07-19_2215__adae04e10233151a__adae04e10233151a.zip", "6º opt taich TOCAR EL CIELO  Y ALCANZAR EL FONDO DEL MAR.mp4", "37_1-optimizadores-de-taichi-la-danza-del-arco-irisx6_opt_taich_TOCAR_EL_CIELO_Y_ALCANZAR_EL_FONDO_DEL_MAR"),
    ("wetransfer_curso37_7o-opt-taich-bombeos-mp4_2026-07-20_1135__f0232f8d88590c18__f0232f8d88590c18.zip", "7º opt taich BOMBEOS.mp4", "37_7-opt-taich-bombeosx7_opt_taich_BOMBEOS"),
    ("wetransfer_curso37_7o-opt-taich-bombeos-mp4_2026-07-20_1135__f0232f8d88590c18__f0232f8d88590c18.zip", "8º OPT TAICH pendulos, abanicos, lanzamientos.mp4", "37_7-opt-taich-bombeosx8_OPT_TAICH_pendulos_abanicos_lanzamientos"),
    ("wetransfer_curso37_7o-opt-taich-bombeos-mp4_2026-07-20_1135__f0232f8d88590c18__f0232f8d88590c18.zip", "9º opt de taich LA DANZA DEL TAO.mp4", "37_7-opt-taich-bombeosx9_opt_de_taich_LA_DANZA_DEL_TAO"),
    ("wetransfer_curso37_7o-opt-taich-bombeos-mp4_2026-07-20_1135__f0232f8d88590c18__f0232f8d88590c18.zip", "20 peng.mp4", "37_7-opt-taich-bombeosx20_peng"),
    ("wetransfer_curso37_directo-estudio-profundo-de-la-gran-rueda-wmv_2026-07-21_2013__fdebaf90ebbdbb17__fdebaf90ebbdbb17.zip", "DIRECTO estudio profundo de la gran rueda.wmv", "37_directo-estudio-profundo-de-la-gran-ruedaxDIRECTO_estudio_profundo_de_la_gran_rueda"),
    ("wetransfer_directo-estudio-prof-sobre-la-danza-del-arco-iris-wmv_2026-07-22_1402__b4d875f3b34fd334__b4d875f3b34fd334.zip", "directo estudio prof sobre la danza del arco iris.wmv", "directo-estudio-prof-sobre-la-danza-del-arco-irisxdirecto_estudio_prof_sobre_la_danza_del_arco_iris"),
    ("wetransfer_estas-son-promocinales-son-6_2026-07-28_1039__0c10ca636f4c4fc1__0c10ca636f4c4fc1.zip", "CHINNA EN ( Si Zheng Tui).mov", "estas-son-promocinales-son-6xCHINNA_EN_Si_Zheng_Tui"),
    ("wetransfer_estas-son-promocinales-son-6_2026-07-28_1039__0c10ca636f4c4fc1__0c10ca636f4c4fc1.zip", "COMPRENDIENDO EL PEQUEÑO TAICHI 1 (An).mp4", "estas-son-promocinales-son-6xCOMPRENDIENDO_EL_PEQUENO_TAICHI_1_An"),
    ("wetransfer_estas-son-promocinales-son-6_2026-07-28_1039__0c10ca636f4c4fc1__0c10ca636f4c4fc1.zip", "COMPRENDIENDO EL PEQUEÑO TAICHI 1 (Peng).mp4", "estas-son-promocinales-son-6xCOMPRENDIENDO_EL_PEQUENO_TAICHI_1_Peng"),
    ("wetransfer_estas-son-promocinales-son-6_2026-07-28_1039__0c10ca636f4c4fc1__0c10ca636f4c4fc1.zip", "ESTILO LIBRE (lan Que Wei) improvisación de ejemplos.mp4", "estas-son-promocinales-son-6xESTILO_LIBRE_lan_Que_Wei_improvisacion_de_ejemplos"),
    ("wetransfer_estas-son-promocinales-son-6_2026-07-28_1039__0c10ca636f4c4fc1__0c10ca636f4c4fc1.zip", "LAS 8 POSICIONES BÁSICAS DEL TAICHI.mp4", "estas-son-promocinales-son-6xLAS_8_POSICIONES_BASICAS_DEL_TAICHI"),
    ("wetransfer_estas-son-promocinales-son-6_2026-07-28_1039__0c10ca636f4c4fc1__0c10ca636f4c4fc1.zip", "TAICHI CHINNA (Cuello de dragón)2º parte.mp4", "estas-son-promocinales-son-6xTAICHI_CHINNA_Cuello_de_dragon_2_parte"),
]


@pytest.mark.parametrize("archive,filename,expected", REFERENCE_CASES)
def test_reference_tree_names_are_reproduced(archive: str, filename: str, expected: str) -> None:
    root = Path("extract")
    source = root / Path(archive).stem / filename
    metadata = FileNameFormatter.resolve_source_metadata(source, root)
    assert metadata.output_stem == expected
