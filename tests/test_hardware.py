from src import hardware


def test_amd_detection_does_not_probe_or_select_cuda(monkeypatch) -> None:
    def which(name: str):
        return "/usr/bin/rocm-smi" if name == "rocm-smi" else None

    monkeypatch.setattr(hardware.shutil, "which", which)
    monkeypatch.setattr(
        hardware.subprocess,
        "check_output",
        lambda *args, **kwargs: "Card series: Radeon Test\nTotal Memory (B): 17179869184\nUsed Memory (B): 4294967296\n",
    )
    gpu = hardware._amd_gpu()
    assert gpu is not None
    assert gpu.vendor == "AMD"
    assert gpu.backend == "rocm"
    assert gpu.usable_for_whisper is False
    assert gpu.whisper_device is None
    assert "not verified" in (gpu.reason or "")


def test_nvidia_probe_requires_ct2_cuda_capability(monkeypatch) -> None:
    monkeypatch.setattr(hardware.shutil, "which", lambda name: "/usr/bin/nvidia-smi" if name == "nvidia-smi" else None)
    monkeypatch.setattr(
        hardware.subprocess,
        "run",
        lambda *args, **kwargs: type("Result", (), {"stdout": "0, RTX Test, 8192, 4096, 555.00\n"})(),
    )
    monkeypatch.setattr(hardware, "_probe_ctranslate2_gpu", lambda _index: (False, "4.8.2", None, "runtime unavailable"))
    gpu = hardware._nvidia_gpu()
    assert gpu.available is True
    assert gpu.vendor == "NVIDIA"
    assert gpu.usable_for_whisper is False
    assert gpu.whisper_device is None
    assert gpu.reason == "runtime unavailable"
