from config.settings import AppSettings
from src.hardware import GPUInfo, HardwareInfo
from src.resource_profile import build_profile, safe_parallelism


def hardware(*, cpu=16, ram=32.0, available=24.0, gpu=None, disk=100.0):
    return HardwareInfo(cpu, max(1, cpu // 2), ram, available, gpu or GPUInfo(False), disk)


def test_auto_without_gpu_uses_cpu_int8():
    settings = AppSettings(whisper_model="auto", whisper_device="auto", whisper_compute_type="auto")
    profile = build_profile(settings, hardware())
    assert profile.whisper_device == "cpu"
    assert profile.whisper_compute_type == "int8"


def test_auto_uses_cuda_only_when_runtime_is_usable():
    gpu = GPUInfo(available=True, vendor="NVIDIA", model="RTX Test", device_index=0, count=1,
                  vram_total_gb=12.0, vram_free_gb=10.0, driver_version="test", runtime="test",
                  backend="cuda", usable_for_whisper=True)
    settings = AppSettings(whisper_model="auto", whisper_device="auto", whisper_compute_type="auto")
    profile = build_profile(settings, hardware(gpu=gpu))
    assert profile.whisper_device == "cuda"
    assert profile.whisper_compute_type == "float16"


def test_detected_gpu_without_runtime_is_not_selected():
    gpu = GPUInfo(available=True, vendor="AMD", model="Radeon Test", backend="rocm",
                  usable_for_whisper=False, reason="CTranslate2 GPU unavailable")
    settings = AppSettings(whisper_model="auto", whisper_device="auto", whisper_compute_type="auto")
    profile = build_profile(settings, hardware(gpu=gpu))
    assert profile.whisper_device == "cpu"


def test_amd_gpu_can_be_selected_when_runtime_probe_is_successful():
    gpu = GPUInfo(available=True, vendor="AMD", model="Radeon Test", device_index=0, count=1,
                  vram_total_gb=16.0, vram_free_gb=12.0, runtime="test", backend="rocm",
                  usable_for_whisper=True, whisper_device="cuda")
    settings = AppSettings(whisper_model="medium", whisper_device="auto", whisper_compute_type="auto")
    profile = build_profile(settings, hardware(gpu=gpu))
    assert profile.whisper_device == "cuda"
    assert profile.whisper_compute_type == "float16"


def test_apple_unified_memory_is_not_double_counted_as_vram():
    gpu = GPUInfo(available=True, vendor="Apple", model="Apple Silicon GPU", device_index=0, count=1,
                  backend="metal", usable_for_whisper=False, memory_model="unified",
                  memory_shared_with_system=True, reason="Metal backend unavailable")
    profile = build_profile(AppSettings(whisper_model="medium"), hardware(cpu=10, ram=16.0, available=6.0, gpu=gpu))
    assert profile.whisper_device == "cpu"
    assert profile.gpu_vram_gb == 4.0


def test_unified_memory_gpu_budget_uses_available_system_memory():
    gpu = GPUInfo(available=True, vendor="Apple", model="Apple Silicon GPU", backend="metal",
                  usable_for_whisper=True, memory_model="unified", memory_shared_with_system=True)
    settings = AppSettings(whisper_model="medium", whisper_device="auto", whisper_compute_type="auto")
    profile = build_profile(settings, hardware(cpu=12, ram=32.0, available=10.0, gpu=gpu))
    assert profile.whisper_device == "cuda"
    assert profile.gpu_vram_gb == 8.0


def test_explicit_cuda_requires_usable_runtime():
    settings = AppSettings(whisper_device="cuda")
    try:
        build_profile(settings, hardware())
    except RuntimeError as exc:
        assert "CUDA" in str(exc)
    else:
        raise AssertionError("explicit CUDA must fail when the runtime is unavailable")


def test_parallelism_is_limited_by_cpu_and_ram_budget():
    settings = AppSettings(whisper_model="medium", whisper_device="cpu", whisper_cpu_threads=8, max_parallel_videos=8)
    effective = safe_parallelism(settings, hardware(cpu=16, ram=16.0, available=10.0))
    assert effective == 1
