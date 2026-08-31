from __future__ import annotations

import logging
import os
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
    gpu_memory_available_gb: float = 0.0
    gpu_memory_model: str = "dedicated"
    gpu_memory_shared_with_system: bool = False
    disk_free_gb: float = 0.0


def _memory_gb() -> float:
    """Return detected physical memory and preserve the legacy injectable seam."""
    return detect_hardware().memory_total_gb


def estimate_whisper_budget(model: str, device: str, threads: int) -> ResourceBudget:
    ram = {"tiny": 0.8, "base": 1.0, "small": 1.6, "medium": 3.0, "large": 5.5, "large-v3": 5.5}.get(model.lower(), 3.0)
    if device == "cuda":
        return ResourceBudget(max(1, threads), 1.5, True, max(2.0, ram * 0.85), 0.0)
    return ResourceBudget(max(1, threads), ram, False, 0.0, 0.0)


def available_gpu_memory(hw: HardwareInfo) -> float:
    """Return safe GPU memory without double-counting system-shared memory."""
    gpu = hw.gpu
    if gpu.memory_shared_with_system or gpu.memory_model in {"unified", "shared"}:
        return max(0.0, hw.memory_available_gb - 2.0)
    return max(0.0, gpu.vram_free_gb)


_available_gpu_memory = available_gpu_memory


def _resolve_whisper(hardware: HardwareInfo, settings: AppSettings) -> tuple[str, str]:
    requested_device = settings.whisper_device.lower().strip()
    requested_compute = settings.whisper_compute_type.lower().strip()
    if requested_device not in {"auto", "cpu", "cuda"}:
        raise ValueError("whisper_device must be one of: auto, cpu, cuda")
    gpu_memory = available_gpu_memory(hardware)
    if requested_device == "cuda":
        if not hardware.gpu.usable_for_whisper:
            raise RuntimeError(
                f"CUDA was explicitly requested but is unavailable: {hardware.gpu.reason or 'unknown reason'}"
            )
        if gpu_memory < 3.0:
            raise RuntimeError(
                f"CUDA was explicitly requested but available GPU memory is insufficient: {gpu_memory:.2f} GB"
            )
        device = "cuda"
    elif requested_device == "cpu":
        device = "cpu"
    else:
        device = "cuda" if hardware.gpu.usable_for_whisper and gpu_memory >= 3.0 else "cpu"
    compute = requested_compute
    if compute == "auto":
        compute = "float16" if device == "cuda" else "int8"
    if device == "cpu" and compute not in {"int8", "int8_float32", "float32"}:
        compute = "int8"
    if device == "cuda" and compute not in {"float16", "int8_float16", "int8_float32", "float32"}:
        compute = "float16"
    return device, compute


def safe_parallelism(settings: AppSettings, hardware: HardwareInfo | None = None) -> int:
    requested = max(1, int(settings.max_parallel_videos))
    if requested == 1:
        return 1
    hw = hardware or detect_hardware()
    device = settings.whisper_device.lower()
    if device == "auto":
        device = "cuda" if hw.gpu.usable_for_whisper and available_gpu_memory(hw) >= 3.0 else "cpu"
    threads = settings.whisper_cpu_threads if settings.whisper_cpu_threads > 0 else max(2, min(8, hw.logical_cpus // 2))
    budget = estimate_whisper_budget(settings.whisper_model, device, threads)
    safe_cpu = max(1, hw.logical_cpus - 2)
    safe_ram = max(1.0, hw.memory_available_gb - 2.0)
    by_cpu = max(1, safe_cpu // max(1, budget.cpu_threads))
    by_ram = max(1, int(safe_ram // max(0.5, budget.ram_gb)))
    by_gpu = requested if device != "cuda" else max(1, int(available_gpu_memory(hw) // max(0.5, budget.gpu_memory_gb)))
    effective = min(requested, by_cpu, by_ram, by_gpu)
    if effective < requested:
        logging.getLogger(__name__).warning(
            "Clamping max_parallel_videos from %d to %d for safe resource budget", requested, effective
        )
    return effective


def build_profile(settings: AppSettings, hardware: HardwareInfo | None = None) -> ResourceProfile:
    hw = hardware or detect_hardware()
    device, compute = _resolve_whisper(hw, settings)
    memory = hw.memory_total_gb
    available = hw.memory_available_gb
    cpus = hw.logical_cpus
    model = settings.whisper_model.lower()
    if model == "auto":
        model = (
            "medium"
            if (device == "cuda" and available_gpu_memory(hw) >= 8) or (memory >= 16 and cpus >= 6)
            else "small"
        )
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
    configured_parallel = 1 if settings.max_parallel_videos <= 0 else max(1, settings.max_parallel_videos)
    effective_parallel = safe_parallelism(replace(settings, max_parallel_videos=configured_parallel), hw)
    return ResourceProfile(
        name,
        cpus,
        hw.physical_cpus,
        memory,
        available,
        model,
        device,
        compute,
        threads,
        effective_parallel,
        settings.translation_batch_size if settings.translation_batch_size > 0 else batch,
        hw.gpu.device_index,
        hw.gpu.vram_free_gb,
        available_gpu_memory(hw),
        hw.gpu.memory_model,
        hw.gpu.memory_shared_with_system,
        hw.disk_free_gb,
    )


def detect_profile(settings: AppSettings) -> ResourceProfile:
    """Build a profile while preserving deterministic CPU/memory test seams."""
    hardware = detect_hardware()
    detected_memory = _memory_gb()
    detected_cpus = max(1, os.cpu_count() or hardware.logical_cpus)
    if detected_memory != hardware.memory_total_gb or detected_cpus != hardware.logical_cpus:
        hardware = replace(
            hardware,
            logical_cpus=detected_cpus,
            memory_total_gb=detected_memory,
            memory_available_gb=min(hardware.memory_available_gb, detected_memory),
        )
    return build_profile(settings, hardware)


def apply_resource_profile(settings: AppSettings, hardware: HardwareInfo | None = None) -> AppSettings:
    if not settings.auto_tune_resources:
        return settings
    hw = hardware or detect_hardware()
    profile = build_profile(settings, hw)
    return replace(
        settings,
        whisper_model=profile.whisper_model,
        whisper_device=profile.whisper_device if settings.whisper_device.lower() == "auto" else settings.whisper_device,
        whisper_compute_type=profile.whisper_compute_type
        if settings.whisper_compute_type.lower() == "auto"
        else settings.whisper_compute_type,
        whisper_cpu_threads=profile.whisper_threads
        if settings.whisper_cpu_threads <= 0
        else settings.whisper_cpu_threads,
        max_parallel_videos=profile.max_parallel_videos,
        translation_batch_size=profile.translation_batch_size,
        resource_profile=profile.name,
        detected_logical_cpus=profile.logical_cpus,
        detected_memory_gb=round(profile.memory_gb, 2),
        detected_memory_available_gb=round(profile.available_memory_gb, 2),
        detected_gpu_vendor=hw.gpu.vendor or "none",
        detected_gpu_model=hw.gpu.model,
        detected_gpu_index=profile.gpu_index if profile.gpu_index is not None else -1,
        detected_gpu_vram_gb=round(profile.gpu_vram_gb, 2),
        detected_gpu_usable=hw.gpu.usable_for_whisper,
        detected_disk_free_gb=round(profile.disk_free_gb, 2),
    )
