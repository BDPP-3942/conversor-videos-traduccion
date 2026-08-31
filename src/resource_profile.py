from __future__ import annotations

from dataclasses import dataclass, replace

from config.settings import AppSettings
from src.hardware import HardwareInfo, detect_hardware


@dataclass(frozen=True)
class ResourceBudget:
    cpu_threads: int
    ram_gb: float
    gpu_required: bool
    gpu_memory_gb: float
    disk_required_gb: float
    purpose: str = "estimate"


@dataclass(frozen=True)
class ResourceProfile:
    name: str
    logical_cpus: int
    physical_cpus: int | None
    memory_gb: float
    available_memory_gb: float
    whisper_model: str
    whisper_device: str
    whisper_compute_type: str
    whisper_threads: int
    max_parallel_videos: int
    translation_batch_size: int
    gpu_index: int | None = None
    gpu_vram_gb: float = 0.0
    disk_free_gb: float = 0.0


def estimate_whisper_budget(model: str, device: str, threads: int) -> ResourceBudget:
    # Conservative initial estimates, intentionally marked as estimates. They are
    # planning guards, not claims about exact model RSS/VRAM consumption.
    ram = {"tiny": 0.8, "base": 1.0, "small": 1.6, "medium": 3.0, "large": 5.5, "large-v3": 5.5}.get(model.lower(), 3.0)
    if device == "cuda":
        return ResourceBudget(max(1, threads), 1.5, True, max(2.0, ram * 0.85), 0.0)
    return ResourceBudget(max(1, threads), ram, False, 0.0, 0.0)


def _resolve_whisper(hardware: HardwareInfo, settings: AppSettings) -> tuple[str, str]:
    requested_device = settings.whisper_device.lower().strip()
    requested_compute = settings.whisper_compute_type.lower().strip()
    if requested_device not in {"auto", "cpu", "cuda"}:
        raise ValueError("whisper_device must be one of: auto, cpu, cuda")
    if requested_device == "cuda":
        if not hardware.gpu.usable_for_whisper:
            raise RuntimeError(f"CUDA was explicitly requested but is unavailable: {hardware.gpu.reason or 'unknown reason'}")
        device = "cuda"
    elif requested_device == "cpu":
        device = "cpu"
    else:
        device = "cuda" if hardware.gpu.usable_for_whisper and hardware.gpu.vram_free_gb >= 3.0 else "cpu"

    if requested_compute == "auto":
        compute = "float16" if device == "cuda" else "int8"
    else:
        compute = requested_compute
    allowed_cpu = {"int8", "int8_float32", "float32"}
    allowed_cuda = {"float16", "int8_float16", "int8_float32", "float32"}
    if device == "cpu" and compute not in allowed_cpu:
        compute = "int8"
    if device == "cuda" and compute not in allowed_cuda:
        compute = "float16"
    return device, compute


def build_profile(settings: AppSettings, hardware: HardwareInfo | None = None) -> ResourceProfile:
    hw = hardware or detect_hardware()
    device, compute = _resolve_whisper(hw, settings)
    memory = hw.memory_total_gb
    available = hw.memory_available_gb
    cpus = hw.logical_cpus
    model = settings.whisper_model.lower()
    if model == "auto":
        if device == "cuda" and hw.gpu.vram_free_gb >= 8:
            model = "medium"
        elif memory >= 16 and cpus >= 6:
            model = "medium"
        else:
            model = "small"

    if memory >= 24 and cpus >= 12:
        name, batch = "high", 12
        default_threads = min(8, max(4, cpus // 2))
    elif memory >= 14 and cpus >= 6:
        name, batch = "balanced", 10
        default_threads = min(6, max(3, cpus // 2))
    else:
        name, batch = "low", 6
        default_threads = min(4, max(2, cpus - 1))

    threads = default_threads if settings.whisper_cpu_threads <= 0 else max(1, settings.whisper_cpu_threads)
    # One video remains the safe default: FFmpeg, Python and Whisper can overlap,
    # so worker count is not derived from CPU count.
    parallel = 1 if settings.max_parallel_videos <= 0 else max(1, settings.max_parallel_videos)
    if parallel > 1:
        budget = estimate_whisper_budget(model, device, threads)
        safe_cpu = max(1, cpus - 2)
        safe_ram = max(1.0, available - 2.0)
        if parallel * budget.cpu_threads > safe_cpu or parallel * budget.ram_gb > safe_ram:
            parallel = max(1, min(parallel, safe_cpu // max(1, budget.cpu_threads)))
            parallel = max(1, min(parallel, int(safe_ram // max(0.5, budget.ram_gb))))
    return ResourceProfile(
        name=name,
        logical_cpus=cpus,
        physical_cpus=hw.physical_cpus,
        memory_gb=memory,
        available_memory_gb=available,
        whisper_model=model,
        whisper_device=device,
        whisper_compute_type=compute,
        whisper_threads=threads,
        max_parallel_videos=parallel,
        translation_batch_size=settings.translation_batch_size if settings.translation_batch_size > 0 else batch,
        gpu_index=hw.gpu.device_index,
        gpu_vram_gb=hw.gpu.vram_free_gb,
        disk_free_gb=hw.disk_free_gb,
    )


def detect_profile(settings: AppSettings) -> ResourceProfile:
    return build_profile(settings)


def apply_resource_profile(settings: AppSettings, hardware: HardwareInfo | None = None) -> AppSettings:
    if not settings.auto_tune_resources:
        return settings
    profile = build_profile(settings, hardware)
    model = profile.whisper_model if settings.whisper_model.lower() == "auto" else settings.whisper_model
    threads = profile.whisper_threads if settings.whisper_cpu_threads <= 0 else settings.whisper_cpu_threads
    parallel = profile.max_parallel_videos if settings.max_parallel_videos <= 0 else profile.max_parallel_videos
    batch = profile.translation_batch_size if settings.translation_batch_size <= 0 else settings.translation_batch_size
    return replace(
        settings,
        whisper_model=model,
        whisper_device=profile.whisper_device if settings.whisper_device.lower() == "auto" else settings.whisper_device,
        whisper_compute_type=profile.whisper_compute_type if settings.whisper_compute_type.lower() == "auto" else settings.whisper_compute_type,
        whisper_cpu_threads=threads,
        max_parallel_videos=parallel,
        translation_batch_size=batch,
        resource_profile=profile.name,
        detected_logical_cpus=profile.logical_cpus,
        detected_memory_gb=round(profile.memory_gb, 2),
        detected_memory_available_gb=round(profile.available_memory_gb, 2),
        detected_gpu_vendor=profile_gpu_vendor(hardware or detect_hardware()),
        detected_gpu_model=(hardware or detect_hardware()).gpu.model,
        detected_gpu_index=profile.gpu_index if profile.gpu_index is not None else -1,
        detected_gpu_vram_gb=round(profile.gpu_vram_gb, 2),
        detected_gpu_usable=(hardware or detect_hardware()).gpu.usable_for_whisper,
        detected_disk_free_gb=round(profile.disk_free_gb, 2),
    )


def profile_gpu_vendor(hardware: HardwareInfo) -> str:
    return hardware.gpu.vendor or "none"
