from __future__ import annotations

import argparse

from src.local_translation import LocalTranslationModelManager


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Gestiona el modelo local de traducción sin conexión fijado por el proyecto"
    )
    parser.add_argument("action", choices=("status", "download", "cleanup"))
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Confirma la descarga del modelo sin solicitar confirmación interactiva",
    )
    args = parser.parse_args()

    manager = LocalTranslationModelManager()
    status = manager.status()
    if args.action == "status":
        print(f"available={status.available}")
        print(f"resource={status.repository}@{status.revision}")
        print(f"license={status.license}")
        print(f"destination={status.path}")
        print(f"approximate_size_mib={status.expected_size_bytes / 1024**2:.1f}")
        if status.reason:
            print(f"reason={status.reason}")
        return 0 if status.available else 1

    if args.action == "cleanup":
        manager.cleanup()
        print(f"removed={manager.model_dir}")
        return 0

    if status.available:
        print(f"already_available={status.path}")
        return 0
    print(f"resource={status.repository}@{status.revision}")
    print(f"version_or_revision={status.revision}")
    print(f"approximate_size_mib={status.expected_size_bytes / 1024**2:.1f}")
    print(f"destination={status.path}")
    print("reason=preparar el proveedor de traducción local para el procesamiento sin conexión")
    print(f"license={status.license}")
    if not args.yes:
        answer = input("¿Descargar ahora este recurso? [s/N] ").strip().lower()
        if answer not in {"s", "si", "sí", "y", "yes"}:
            print("Descarga cancelada.")
            return 2
    manager.download()
    final = manager.status()
    if not final.available:
        print(f"La descarga ha terminado, pero la validación ha fallado: {final.reason}")
        return 1
    print(f"ready={final.path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
