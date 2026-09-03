from types import SimpleNamespace

import src.cuda_runtime as cuda_runtime


def test_cuda_runtime_reports_no_nvidia(monkeypatch):
    monkeypatch.setattr(cuda_runtime.shutil, "which", lambda name: None)
    status = cuda_runtime.inspect_cuda_runtime()
    assert status.nvidia_gpu is False
    assert status.compatible is False


def test_cuda_runtime_requires_runtime_libraries(monkeypatch):
    monkeypatch.setattr(cuda_runtime.shutil, "which", lambda name: "/usr/bin/nvidia-smi" if name == "nvidia-smi" else None)
    monkeypatch.setattr(cuda_runtime, "_run", lambda command: (0, "530.00\n" if "query-gpu" in command else "CUDA Version: 12.8"))
    monkeypatch.setattr(cuda_runtime, "_detect_toolkit", lambda: ("12.8", "/usr/local/cuda"))
    monkeypatch.setattr(cuda_runtime, "_package_version", lambda name: None)
    monkeypatch.setattr(cuda_runtime, "_library_candidates", lambda: ([], []))
    status = cuda_runtime.inspect_cuda_runtime()
    assert status.nvidia_gpu is True
    assert status.compatible is False
    assert "Missing NVIDIA runtime libraries" in status.reason


def test_cuda_runtime_accepts_verified_ctranslate2(monkeypatch):
    monkeypatch.setattr(cuda_runtime.shutil, "which", lambda name: "/usr/bin/nvidia-smi" if name == "nvidia-smi" else None)
    monkeypatch.setattr(cuda_runtime, "_run", lambda command: (0, "530.00\n" if "query-gpu" in command else "CUDA Version: 12.8"))
    monkeypatch.setattr(cuda_runtime, "_detect_toolkit", lambda: ("12.8", "/usr/local/cuda"))
    versions = {"nvidia-cublas-cu12": "12.8.3.14", "nvidia-cudnn-cu12": "9.7.1.26", "ctranslate2": "4.8.2", "faster-whisper": "1.2.1"}
    monkeypatch.setattr(cuda_runtime, "_package_version", lambda name: versions.get(name))
    monkeypatch.setattr(cuda_runtime, "_library_candidates", lambda: ([], []))
    fake_ct2 = SimpleNamespace(get_cuda_device_count=lambda: 1, get_supported_compute_types=lambda device, index: {"float16", "int8_float16"})
    monkeypatch.setitem(__import__("sys").modules, "ctranslate2", fake_ct2)
    status = cuda_runtime.inspect_cuda_runtime()
    assert status.compatible is True
