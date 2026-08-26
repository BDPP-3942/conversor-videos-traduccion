from __future__ import annotations

import os
import platform
import sys
from dataclasses import dataclass, replace

from config.settings import AppSettings


@dataclass(frozen=True)
class ResourceProfile:
    name: str
    logical_cpus: int
    memory_gb: float
    whisper_model: str
    whisper_threads: int
    max_parallel_videos: int
    translation_batch_size: int


def _memory_gb() -> float:
    system = platform.system()
    try:
        if system == "Windows":
            import ctypes

            class MemoryStatus(ctypes.Structure):
                _fields_ = [
                    ("length", ctypes.c_ulong),
                    ("memory_load", ctypes.c_ulong),
                    ("total_phys", ctypes.c_ulonglong),
                    ("avail_phys", ctypes.c_ulonglong),
                    ("total_page", ctypes.c_ulonglong),
                    ("avail_page", ctypes.c_ulonglong),
                    ("total_virtual", ctypes.c_ulonglong),
                    ("avail_virtual", ctypes.c_ulonglong),
                    ("avail_ext_virtual", ctypes.c_ulonglong),
                ]

            status = MemoryStatus()
            status.length = ctypes.sizeof(MemoryStatus)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
                return status.total_phys / 1024**3
        elif system == "Darwin":
            page_size = int(os.sysconf("SC_PAGE_SIZE"))
            physical_pages = int(os.sysconf("SC_PHYS_PAGES"))
            return page_size * physical_pages / 1024**3
        elif system == "Linux":
            with open("/proc/meminfo", encoding="utf-8") as handle:
                for line in handle:
                    if line.startswith("MemTotal:"):
                        return int(line.split()[1]) / 1024**2
    except (OSError, ValueError):
        pass
    return 8.0


def detect_profile(settings: AppSettings) -> ResourceProfile:
    cpus = max(1, os.cpu_count() or 1)
    memory = _memory_gb()
    arch = platform.machine().lower()
    arm64 = sys.platform == "darwin" and arch in {"arm64", "aarch64"}

    if memory >= 24 and cpus >= 12:
        name = "high"
        model = "medium"
        threads = min(12, max(8, cpus - 4))
        parallel = 1
        batch = 12
    elif memory >= 14 and cpus >= 6:
        name = "balanced"
        model = "medium" if arm64 or memory >= 16 else "small"
        threads = min(8, max(4, cpus - 2))
        parallel = 1
        batch = 10
    else:
        name = "low"
        model = "small"
        threads = min(4, max(2, cpus - 1))
        parallel = 1
        batch = 6

    return ResourceProfile(name, cpus, memory, model, threads, parallel, batch)


def apply_resource_profile(settings: AppSettings) -> AppSettings:
    if not settings.auto_tune_resources:
        return settings
    profile = detect_profile(settings)
    model = profile.whisper_model if settings.whisper_model.lower() == "auto" else settings.whisper_model
    threads = profile.whisper_threads if settings.whisper_cpu_threads <= 0 else settings.whisper_cpu_threads
    parallel = profile.max_parallel_videos if settings.max_parallel_videos <= 0 else settings.max_parallel_videos
    batch = profile.translation_batch_size if settings.translation_batch_size <= 0 else settings.translation_batch_size
    return replace(
        settings,
        whisper_model=model,
        whisper_cpu_threads=threads,
        max_parallel_videos=parallel,
        translation_batch_size=batch,
        resource_profile=profile.name,
        detected_logical_cpus=profile.logical_cpus,
        detected_memory_gb=round(profile.memory_gb, 2),
    )
