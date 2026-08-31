from config.settings import AppSettings
from src.hardware import GPUInfo, HardwareInfo
from src.pipeline import MediaPipeline
from src.resource_profile import safe_parallelism


def _hardware() -> HardwareInfo:
    return HardwareInfo(
        logical_cpus=16,
        physical_cpus=8,
        memory_total_gb=32.0,
        memory_available_gb=30.0,
        gpu=GPUInfo(False),
        disk_free_gb=100.0,
    )


def test_pipeline_clamps_excessive_cli_override(monkeypatch):
    settings = AppSettings(
        provider="local",
        whisper_model="medium",
        whisper_device="cpu",
        whisper_compute_type="int8",
        whisper_cpu_threads=4,
        max_parallel_videos=999,
    )
    hardware = _hardware()
    monkeypatch.setattr("src.pipeline.safe_parallelism", lambda value: safe_parallelism(value, hardware))
    pipeline = object.__new__(MediaPipeline)
    pipeline.settings = settings
    assert pipeline._effective_parallelism() == 3


def test_pipeline_preserves_single_worker(monkeypatch):
    settings = AppSettings(
        provider="local",
        whisper_model="medium",
        whisper_device="cpu",
        whisper_compute_type="int8",
        whisper_cpu_threads=4,
        max_parallel_videos=1,
    )
    hardware = _hardware()
    monkeypatch.setattr("src.pipeline.safe_parallelism", lambda value: safe_parallelism(value, hardware))
    pipeline = object.__new__(MediaPipeline)
    pipeline.settings = settings
    assert pipeline._effective_parallelism() == 1
