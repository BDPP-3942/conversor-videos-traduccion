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
    count: int = 0
    vram_total_gb: float = 0.0
    vram_free_gb: float = 0.0
    driver_version: str | None = None
    runtime: str | None = None
    backend: str | None = None
    usable_for_whisper: bool = False
    reason: str | None = None
    memory_model: str = "dedicated"
    memory_shared_with_system: bool = False
    whisper_device: str | None = None


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
                _fields_ = [
                    ("length", ctypes.c_ulong), ("memory_load", ctypes.c_ulong),
                    ("total_phys", ctypes.c_ulonglong), ("avail_phys", ctypes.c_ulonglong),
                    ("total_page", ctypes.c_ulonglong), ("avail_page", ctypes.c_ulonglong),
                    ("total_virtual", ctypes.c_ulonglong), ("avail_virtual", ctypes.c_ulonglong),
                    ("avail_ext_virtual", ctypes.c_ulonglong),
                ]

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
            return total, _darwin_available_memory(page_size, total)
    except (OSError, ValueError, AttributeError):
        pass
    return 8.0, 8.0


def _darwin_available_memory(page_size: int, total_gb: float) -> float:
    binary = shutil.which("vm_stat")
    if not binary:
        return max(0.0, total_gb * 0.5)
    try:
        output = subprocess.check_output([binary], text=True, stderr=subprocess.DEVNULL, timeout=2)
        pages: dict[str, int] = {}
        for line in output.splitlines():
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            value = value.strip().rstrip(".")
            if value.isdigit():
                pages[key] = int(value)
        free_pages = sum(pages.get(key, 0) for key in ("Pages free", "Pages inactive", "Pages speculative"))
        return max(0.0, min(total_gb, free_pages * page_size / 1024**3))
    except (OSError, ValueError, subprocess.SubprocessError):
        return max(0.0, total_gb * 0.5)


def _physical_cpus() -> int | None:
    if platform.system() == "Windows":
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


def _probe_ctranslate2_gpu(device_index: int = 0) -> tuple[bool, str | None, str | None, str | None]:
    """Probe the actual CTranslate2 GPU runtime instead of trusting the driver alone."""
    try:
        import ctranslate2
    except ImportError:
        return False, None, None, "CTranslate2 is not installed"
    runtime = getattr(ctranslate2, "__version__", None)
    try:
        count = int(ctranslate2.get_cuda_device_count())
    except (AttributeError, RuntimeError, TypeError):
        return False, runtime, None, "CTranslate2 GPU capability probe failed"
    if count <= device_index:
        return False, runtime, None, "CTranslate2 reports no usable GPU device"
    try:
        compute_types = ctranslate2.get_supported_compute_types("cuda", device_index)
    except (AttributeError, RuntimeError, TypeError):
        compute_types = set()
    if not compute_types:
        return False, runtime, None, "CTranslate2 reports no supported GPU compute types"
    return True, runtime, "cuda", None


def _nvidia_gpu() -> GPUInfo:
    binary = shutil.which("nvidia-smi")
    if not binary:
        return GPUInfo(False, vendor="NVIDIA", reason="nvidia-smi not available")
    try:
        result = subprocess.run(
            [binary, "--query-gpu=index,name,memory.total,memory.free,driver_version", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=3, check=True,
        )
        rows = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        if not rows:
            return GPUInfo(False, vendor="NVIDIA", reason="nvidia-smi returned no GPU")
        first = [item.strip() for item in rows[0].split(",")]
        if len(first) < 5:
            return GPUInfo(False, vendor="NVIDIA", reason="invalid nvidia-smi output")
        index, total, free = int(first[0]), float(first[2]) / 1024, float(first[3]) / 1024
        usable, runtime, backend, reason = _probe_ctranslate2_gpu(index)
        return GPUInfo(True, "NVIDIA", first[1], index, len(rows), total, free, first[4], runtime, backend,
                       usable, reason, "dedicated", False, "cuda" if usable else None)
    except (OSError, ValueError, subprocess.SubprocessError):
        return GPUInfo(False, vendor="NVIDIA", reason="nvidia-smi query failed")


def _amd_gpu() -> GPUInfo | None:
    binary = shutil.which("rocm-smi")
    rocminfo = shutil.which("rocminfo")
    if not binary and not rocminfo:
        return None
    model = None
    total = free = 0.0
    if binary:
        try:
            output = subprocess.check_output([binary, "--showproductname", "--showmeminfo", "vram"], text=True,
                                             stderr=subprocess.DEVNULL, timeout=4)
            for line in output.splitlines():
                low = line.lower()
                if "card series" in low or "product name" in low:
                    model = line.split(":", 1)[-1].strip()
                if "total memory" in low:
                    total = float(line.split(":", 1)[-1].strip().split()[0]) / 1024**2
                if "used memory" in low:
                    used = float(line.split(":", 1)[-1].strip().split()[0]) / 1024**2
                    free = max(0.0, total - used)
        except (OSError, ValueError, subprocess.SubprocessError):
            pass
    if model is None and rocminfo:
        try:
            output = subprocess.check_output([rocminfo], text=True, stderr=subprocess.DEVNULL, timeout=4)
            for line in output.splitlines():
                stripped = line.strip()
                if stripped.startswith("Name:") and "gfx" not in stripped.lower():
                    model = stripped.split(":", 1)[1].strip()
                    break
        except (OSError, subprocess.SubprocessError):
            pass
    usable, runtime, backend, reason = _probe_ctranslate2_gpu(0)
    return GPUInfo(True, "AMD", model, 0, 1, total, free, runtime=runtime, backend="rocm",
                   usable_for_whisper=usable, reason=reason or "ROCm GPU capability verified by CTranslate2",
                   memory_model="dedicated", memory_shared_with_system=False,
                   whisper_device="cuda" if usable else None)


def _intel_gpu() -> GPUInfo | None:
    binary = shutil.which("xpu-smi") or shutil.which("intel_gpu_top")
    if not binary:
        return None
    return GPUInfo(True, "Intel", backend="xpu", usable_for_whisper=False,
                   reason="Intel GPU detected but Whisper GPU backend is not verified",
                   memory_model="shared_or_dedicated", memory_shared_with_system=False)


def detect_gpu() -> GPUInfo:
    nvidia = _nvidia_gpu()
    if nvidia.available:
        return nvidia
    amd = _amd_gpu()
    if amd is not None:
        return amd
    intel = _intel_gpu()
    if intel is not None:
        return intel
    system = platform.system()
    if system == "Darwin" and platform.machine().lower() in {"arm64", "aarch64"}:
        return GPUInfo(True, "Apple", "Apple Silicon GPU", 0, 1, backend="metal", usable_for_whisper=False,
                       reason="CTranslate2/faster-whisper Metal backend is not verified",
                       memory_model="unified", memory_shared_with_system=True, whisper_device=None)
    return GPUInfo(False, reason="no supported GPU runtime detected")


def detect_hardware(path: Path | None = None) -> HardwareInfo:
    total, available = _memory_info()
    try:
        disk_free = shutil.disk_usage(path or Path.cwd()).free / 1024**3
    except OSError:
        disk_free = 0.0
    return HardwareInfo(max(1, os.cpu_count() or 1), _physical_cpus(), total, available, detect_gpu(), disk_free)
