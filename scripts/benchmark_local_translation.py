from __future__ import annotations

import argparse
import time

from config.loader import load_settings
from src.hardware import detect_hardware
from src.local_translation import LocalTranslationProvider, LocalTranslationModelManager


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark the prepared offline local translation model")
    parser.add_argument("--sentences", type=int, default=100)
    args = parser.parse_args()
    if args.sentences < 1:
        parser.error("--sentences must be >= 1")

    manager = LocalTranslationModelManager()
    status = manager.status()
    if not status.available:
        print(f"model=NOT_READY reason={status.reason}")
        return 2

    settings = load_settings()
    provider = LocalTranslationProvider(settings, manager)
    texts = ["Hola, ¿cómo estás? Esta es una frase de prueba para medir la traducción local."] * args.sentences
    hardware = detect_hardware()
    start = time.perf_counter()
    load_time = time.perf_counter() - start
    start = time.perf_counter()
    outputs = provider.translate_batch(texts)
    total = time.perf_counter() - start
    print(f"model={status.repository}@{status.revision}")
    print(f"hardware={hardware.gpu.vendor or 'none'}:{hardware.gpu.model or 'none'}")
    print(f"ram_gb={hardware.memory_total_gb:.2f}")
    print(f"device={provider.device}")
    print(f"compute_type={provider.compute_type}")
    print(f"input_cues={len(texts)}")
    print(f"input_chars={sum(len(text) for text in texts)}")
    print(f"load_time_seconds={load_time:.6f}")
    print(f"translation_time_seconds={total:.6f}")
    print(f"throughput_cues_per_second={len(outputs) / total:.3f}")
    print(f"time_per_cue_ms={total / len(outputs) * 1000:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
