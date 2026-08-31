from config.settings import AppSettings
from src.hardware import GPUInfo, HardwareInfo
from src.resource_profile import safe_parallelism


def _hardware(*, cpus: int = 16, memory: float = 32.0, available: float = 30.0) -> HardwareInfo:
    return HardwareInfo(
        logical_cpus=cpus,
        physical_cpus=8,
        memory_total_gb=memory,
        memory_available_gb=available,
        gpu=GPUInfo(False),
        disk_free_gb=100.0,
    )


def test_auto_parallelism_uses_resource_budget_instead_of_defaulting_to_one():
    settings = AppSettings(
        whisper_model="medium",
        whisper_device="cpu",
        whisper_compute_type="int8",
        whisper_cpu_threads=4,
        max_parallel_videos=0,
    )

    assert safe_parallelism(settings, _hardware()) == 3


def test_explicit_parallelism_is_an_upper_bound_not_a_resource_override():
    settings = AppSettings(
        whisper_model="medium",
        whisper_device="cpu",
        whisper_compute_type="int8",
        whisper_cpu_threads=4,
        max_parallel_videos=99,
    )

    assert safe_parallelism(settings, _hardware()) == 3


def test_single_worker_remains_single_worker():
    settings = AppSettings(
        whisper_model="medium",
        whisper_device="cpu",
        whisper_compute_type="int8",
        whisper_cpu_threads=4,
        max_parallel_videos=1,
    )

    assert safe_parallelism(settings, _hardware()) == 1
