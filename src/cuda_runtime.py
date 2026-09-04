from __future__ import annotations

import importlib.metadata
import json
import os
import platform
import shutil
import subprocess
import sys
import threading
from dataclasses import dataclass
from pathlib import Path

from config.settings import BASE_DIR

CUDA_MAJOR = 12
CUDNN_MAJOR = 9
CUBLAS_SPEC = "nvidia-cublas-cu12>=12,<13"
CUDNN_SPEC = "nvidia-cudnn-cu12>=9,<10"
MANAGED_DIR = BASE_DIR / "tools" / "cuda"
MANAGED_PYTHON_DIR = MANAGED_DIR / "python"
MANIFEST = MANAGED_DIR / "runtime.json"
_prompt_lock = threading.Lock()
_interactive_decision: bool | None = None


@dataclass(frozen=True)
class CUDARuntimeStatus:
    nvidia_gpu: bool
    driver_version: str | None
    driver_cuda_max: str | None
    toolkit_version: str | None
    toolkit_path: str | None
    cublas_version: str | None
    cudnn_version: str | None
    cublas_available: bool
    cudnn_available: bool
    ctranslate2_version: str | None
    faster_whisper_version: str | None
    compatible: bool
    reason: str
    install_location: str


def _version_tuple(value: str | None) -> tuple[int, ...]:
    if not value:
        return ()
    result: list[int] = []
    for part in value.replace("-", ".").split("."):
        digits = "".join(ch for ch in part if ch.isdigit())
        if not digits:
            break
        result.append(int(digits))
    return tuple(result)


def _add_managed_python_path() -> None:
    if MANAGED_PYTHON_DIR.is_dir() and str(MANAGED_PYTHON_DIR) not in sys.path:
        sys.path.insert(0, str(MANAGED_PYTHON_DIR))


def _package_version(name: str) -> str | None:
    _add_managed_python_path()
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def _run(command: list[str]) -> tuple[int, str]:
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        return result.returncode, f"{result.stdout}\n{result.stderr}"
    except (OSError, subprocess.SubprocessError):
        return 127, ""


def _detect_toolkit() -> tuple[str | None, str | None]:
    nvcc = shutil.which("nvcc")
    if nvcc:
        code, output = _run([nvcc, "--version"])
        if code == 0:
            for line in output.splitlines():
                if "release " in line.lower():
                    version = line.lower().split("release ", 1)[1].split(",", 1)[0].strip()
                    return version, str(Path(nvcc).resolve().parent.parent)
    cuda_path = os.getenv("CUDA_PATH") or os.getenv("CUDA_HOME")
    if cuda_path:
        path = Path(cuda_path)
        version_file = path / "version.json"
        if version_file.is_file():
            try:
                data = json.loads(version_file.read_text(encoding="utf-8"))
                version = data.get("cuda", {}).get("version")
                if version:
                    return str(version), str(path)
            except (OSError, ValueError, TypeError):
                pass
        return None, str(path)
    return None, None


def _library_candidates() -> tuple[list[Path], list[Path]]:
    if platform.system() == "Windows":
        roots = [Path(item) for item in os.getenv("PATH", "").split(os.pathsep) if item]
        cuda_path = os.getenv("CUDA_PATH") or os.getenv("CUDA_HOME")
        if cuda_path:
            roots.append(Path(cuda_path) / "bin")
        managed = MANAGED_PYTHON_DIR / "nvidia"
        roots += [managed / "cublas" / "bin", managed / "cudnn" / "bin"]
        cublas = [root / name for root in roots for name in ("cublas64_12.dll", "cublasLt64_12.dll")]
        cudnn = [root / "cudnn64_9.dll" for root in roots]
    else:
        roots = [Path(item) for item in os.getenv("LD_LIBRARY_PATH", "").split(os.pathsep) if item]
        roots += [Path("/usr/local/cuda/lib64"), Path("/usr/local/cuda/lib")]
        managed = MANAGED_PYTHON_DIR / "nvidia"
        roots += [managed / "cublas" / "lib", managed / "cudnn" / "lib"]
        cublas = [root / "libcublas.so.12" for root in roots]
        cudnn = [root / "libcudnn.so.9" for root in roots]
    return cublas, cudnn


def _prepend_managed_libraries() -> None:
    if platform.system() == "Windows":
        paths = [
            MANAGED_PYTHON_DIR / "nvidia" / "cublas" / "bin",
            MANAGED_PYTHON_DIR / "nvidia" / "cudnn" / "bin",
        ]
        existing = os.getenv("PATH", "").split(os.pathsep)
        os.environ["PATH"] = os.pathsep.join([str(path) for path in paths if path.is_dir()] + existing)
        if hasattr(os, "add_dll_directory"):
            for path in paths:
                if path.is_dir():
                    try:
                        os.add_dll_directory(str(path))
                    except OSError:
                        pass
    else:
        paths = [
            MANAGED_PYTHON_DIR / "nvidia" / "cublas" / "lib",
            MANAGED_PYTHON_DIR / "nvidia" / "cudnn" / "lib",
        ]
        existing = os.getenv("LD_LIBRARY_PATH", "").split(os.pathsep) if os.getenv("LD_LIBRARY_PATH") else []
        os.environ["LD_LIBRARY_PATH"] = os.pathsep.join([str(path) for path in paths if path.is_dir()] + existing)


def inspect_cuda_runtime() -> CUDARuntimeStatus:
    _add_managed_python_path()
    _prepend_managed_libraries()
    nvidia_smi = shutil.which("nvidia-smi")
    nvidia_gpu = nvidia_smi is not None
    driver_version = driver_cuda_max = None
    if nvidia_smi:
        code, output = _run([nvidia_smi, "--query-gpu=driver_version", "--format=csv,noheader"])
        if code == 0:
            driver_version = next((line.strip() for line in output.splitlines() if line.strip()), None)
        code, output = _run([nvidia_smi])
        if code == 0:
            for line in output.splitlines():
                if "CUDA Version" in line:
                    driver_cuda_max = line.split("CUDA Version:", 1)[1].strip().split()[0]
                    break
    toolkit_version, toolkit_path = _detect_toolkit()
    cublas_pkg = _package_version("nvidia-cublas-cu12")
    cudnn_pkg = _package_version("nvidia-cudnn-cu12")
    cublas_files, cudnn_files = _library_candidates()
    cublas_available = cublas_pkg is not None or any(path.is_file() for path in cublas_files)
    cudnn_available = cudnn_pkg is not None or any(path.is_file() for path in cudnn_files)
    ct2 = _package_version("ctranslate2")
    fw = _package_version("faster-whisper")

    common = (
        driver_version,
        driver_cuda_max,
        toolkit_version,
        toolkit_path,
        cublas_pkg,
        cudnn_pkg,
        cublas_available,
        cudnn_available,
        ct2,
        fw,
    )
    if not nvidia_gpu:
        return CUDARuntimeStatus(
            False,
            *common,
            False,
            "No NVIDIA GPU detected",
            str(MANAGED_DIR),
        )
    if driver_cuda_max and _version_tuple(driver_cuda_max)[0:1] < (CUDA_MAJOR,):
        return CUDARuntimeStatus(
            True,
            *common,
            False,
            f"NVIDIA driver advertises CUDA {driver_cuda_max}; CUDA {CUDA_MAJOR}.x is required",
            str(MANAGED_DIR),
        )
    if not cublas_available or not cudnn_available:
        missing = ", ".join(
            name
            for name, ok in (
                ("cuBLAS CUDA 12", cublas_available),
                ("cuDNN 9 CUDA 12", cudnn_available),
            )
            if not ok
        )
        return CUDARuntimeStatus(
            True,
            *common,
            False,
            f"Missing NVIDIA runtime libraries: {missing}",
            str(MANAGED_DIR),
        )
    try:
        import ctranslate2

        count = int(ctranslate2.get_cuda_device_count())
        supported = ctranslate2.get_supported_compute_types("cuda", 0) if count else set()
        if not supported:
            raise RuntimeError("CTranslate2 reports no supported CUDA compute types")
    except (ImportError, AttributeError, RuntimeError, TypeError) as exc:
        return CUDARuntimeStatus(
            True,
            *common,
            False,
            f"CTranslate2 CUDA validation failed: {exc}",
            str(MANAGED_DIR),
        )
    return CUDARuntimeStatus(
        True,
        *common,
        True,
        "CUDA runtime and CTranslate2 capability validated",
        str(MANAGED_DIR),
    )


def install_managed_cuda_runtime() -> CUDARuntimeStatus:
    MANAGED_PYTHON_DIR.mkdir(parents=True, exist_ok=True)
    command = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--disable-pip-version-check",
        "--no-input",
        "--upgrade",
        "--target",
        str(MANAGED_PYTHON_DIR),
        CUBLAS_SPEC,
        CUDNN_SPEC,
    ]
    result = subprocess.run(command, timeout=1800, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"Managed CUDA library installation failed with exit code {result.returncode}")
    _add_managed_python_path()
    _prepend_managed_libraries()
    selected = {name: _package_version(name) for name in ("nvidia-cublas-cu12", "nvidia-cudnn-cu12")}
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    manifest = {
        "cuda_major": CUDA_MAJOR,
        "cudnn_major": CUDNN_MAJOR,
        "packages": selected,
        "python_target": str(MANAGED_PYTHON_DIR),
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return inspect_cuda_runtime()


def ensure_cuda_runtime(*, interactive: bool = True) -> CUDARuntimeStatus:
    global _interactive_decision
    status = inspect_cuda_runtime()
    if not status.nvidia_gpu or status.compatible:
        return status
    if not interactive or not sys.stdin.isatty():
        return status
    with _prompt_lock:
        if _interactive_decision is False:
            return status
        if _interactive_decision is None:
            print(
                "\nNVIDIA GPU detected, but the CUDA runtime required by the pinned "
                "faster-whisper/CTranslate2 stack is not ready."
            )
            print(f"Reason: {status.reason}")
            print(
                f"Detected driver: {status.driver_version or 'unknown'}; "
                f"advertised CUDA: {status.driver_cuda_max or 'unknown'}"
            )
            print(f"Requirements: CUDA {CUDA_MAJOR}.x + cuBLAS for CUDA 12 + cuDNN {CUDNN_MAJOR} for CUDA 12.")
            print(f"Managed installation: {MANAGED_DIR}")
            print(f"Runtime libraries will be installed into: {MANAGED_PYTHON_DIR}")
            print(
                "The NVIDIA driver is not replaced. A full CUDA Toolkit is optional "
                "and is not installed by this operation."
            )
            answer = input("Install the managed NVIDIA runtime libraries now? [y/N]: ").strip().lower()
            _interactive_decision = answer in {"y", "yes"}
        if not _interactive_decision:
            return status
    return install_managed_cuda_runtime()
