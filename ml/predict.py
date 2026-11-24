"""CLI rapido para probar el modelo con una o varias imagenes.

Uso:
    py -3 ml/predict.py ruta/manzana.jpg [otra.png ...]
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PIL import Image

from app.services.inference import InferenceService


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        raise SystemExit(1)

    service = InferenceService(Path(__file__).resolve().parent / "artifacts")
    print(f"backend={service._backend} clases={len(service.labels)}")
    for argument in sys.argv[1:]:
        path = Path(argument)
        with Image.open(path) as image:
            result = service.predict(image)
        print(
            f"{path.name:40} -> {result['display_label']:22} "
            f"{result['confidence'] * 100:6.2f}%  ({result['latency_ms']:.1f} ms)"
        )


if __name__ == "__main__":
    main()
