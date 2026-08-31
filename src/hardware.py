from __future__ import annotations

import os
import platform
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class GPUInfo:
    available: bool
    vendor: str | None = None
    model: str | None = None
    device_index: int | None = None
    vram_total_gb: float = 0.0
    vram_free_gb: float = 0.0
    driver_version: str | None = None
    runtime: str | None = None
    backend: str | None = None
    usable_for_whisper: bool = False
    reason: str | None = None


@dataclass(frozen=True)
class HardwareInfo:
    logical_cpus: int
    physical_cpus: int | None
    memory_total_gb: float
    memory_available_gb: float
    gpu: GPUInfo
    disk_free_gb: float


def _memory_info() -> tuple[float, float]:
    system = platform.system()
    try:
        if system == "Windows":
            import ctypes
            class MemoryStatus(ctypes.Structure):
                _fields_ = [("length", ctypes.c_ulong), ("memory_load", ctypes.c_ulong), ("total_phys", ctypes.c_ulonglong), ("avail_phys", ctypes.c_ulonglong), ("total_page", ctypes.c_ulonglong), ("avail_page", ctypes.c_ulonglong), ("total_virtual", ctypes.c_ulonglong), ("avail_virtual", ctypes.c_ulonglong), ("avail_ext_virtual", ctypes.c_ulonglong)]
            status = MemoryStatus()
            status.length = ctypes.sizeof(MemoryStatus)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
                return status.total_phys / 1024**3, status.avail_phys / 1024**3
        elif system == "Linux":
            values: dict[str, int] = {}
            with open("/proc/meminfo", encoding="utf-8") as handle:
                for line in handle:
                    key, value, *_ = line.split()
                    if key in {"MemTotal:", "MemAvailable:"}:
                        values[key] = int(value)
            if "MemTotal:" in values:
                available = values.get("MemAvailable:", values["MemTotal:"])
                return values["MemTotal:"] / 1024**2, available / 1024**2
        elif system == "Darwin":
            page_size = int(os.sysconf("SC_PAGE_SIZE"))
            physical_pages = int(os.sysconf("SC_PHYS_PAGES"))
            total = page_size * physical_pages / 1024**3
            return total, total
    except (OSError, ValueError, AttributeError):
        pass
    return 8.0, 8.0


def _physical_cpus() -> int | None:
    if platform.system() == "Windows":
        try:
            return int(os.environ.get("NUMBER_OF_PROCESSORS", "1"))
        except ValueError:
            return None
    binary = shutil.which("lscpu")
    if not binary:
        return None
    try:
        output = subprocess.check_output([binary, "-p=CORE"], text=True, stderr=subprocess.DEVNULL, timeout=2)
        cores = {line.strip() for line in output.splitlines() if line.strip() and not line.startswith("#")}
        return len(cores) or None
    except (OSError, ValueError, subprocess.SubprocessError):
        return None


def _nvidia_gpu() -> GPUInfo:
    binary = shutil.which("nvidia-smi")
    if not binary:
        return GPUInfo(False, vendor="NVIDIA", reason="nvidia-smi not available")
    try:
        result = subprocess.run([binary, "--query-gpu=index,name,memory.total,memory.free,driver_version", "--format=csv,noheader,nounits"], capture_output=True, text=True, timeout=3, check=True)
        rows = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        if not rows:
            return GPUInfo(False, vendor="NVIDIA", reason="nvidia-smi returned no GPU")
        first = [item.strip() for item in rows[0].split(",")]
        if len(first) < 5:
            return GPUInfo(False, vendor="NVIDIA", reason="invalid nvidia-smi output")
        index, total, free = int(first[0]), float(first[2]) / 1024, float(first[3]) / 1024
        runtime = None
        usable = False
        reason = "CUDA runtime not verified"
        try:
            import ctranslate2
            runtime = getattr(ctranslate2, "__version__", None)
            usable = int(ctranslate2.get_cuda_device_count()) > index
            reason = None if usable else "CTranslate2 reports no usable CUDA device"
        except (ImportError, AttributeError, RuntimeError):
            reason = "CTranslate2 CUDA capability unavailable"
        return GPUInfo(True, "NVIDIA", first[1], index, total, free, first[4], runtime, "cuda", usable, reason)
    except (OSError, ValueError, subprocess.SubprocessError):
        return GPUInfo(False, vendor="NVIDIA", reason="nvidia-smi query failed")


def detect_gpu() -> GPUInfo:
    nvidia = _nvidia_gpu()
    if nvidia.available:
        return nvidia
    system = platform.system()
    if system == "Darwin" and platform.machine().lower() in {"arm64", "aarch64"}:
        return GPUInfo(True, "Apple", "Apple Silicon GPU", 0, backend="metal", usable_for_whisper=False, reason="faster-whisper backend is not selected for Metal automatically")
    if shutil.which("rocm-smi"):
        return GPUInfo(True, "AMD", None, 0, runtime="ROCm", backend="rocm", usable_for_whisper=False, reason="GPU detected but faster-whisper runtime is not verified")
    return GPUInfo(False, reason="no supported GPU runtime detected")


def detect_hardware(path: Path | None = None) -> HardwareInfo:
    total, available = _memory_info()
    try:
        disk_free = shutil.disk_usage(path or Path.cwd()).free / 1024**3
    except OSError:
        disk_free = 0.0
    return HardwareInfo(max(1, os.cpu_count() or 1), _physical_cpus(), total, available, detect_gpu(), disk_free)
