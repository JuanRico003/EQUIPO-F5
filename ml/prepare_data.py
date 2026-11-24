"""Construye un manifest limpio del dataset.

Problemas que resuelve este script
---------------------------------
1. Nombres inconsistentes entre Train y Test (`freshpotato` vs `freshpatato`,
   `freshtomato` vs `freshtamto`, `bittergroud` vs `bittergourd`).
2. Fuga de datos: ~60 % de Test son copias byte a byte de Train.
3. Duplicados internos (los ficheros `rotated_by_15_*` son copias exactas).

No copia imagenes: genera `data/manifest.csv` con la ruta original, la clase
canonica y el split asignado. Asi el entrenamiento es rapido y no se duplica
el dataset en disco.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import re
from collections import Counter, defaultdict
from pathlib import Path

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".webp"}

# Correcciones de los typos presentes en el dataset original.
CLASS_FIXES = {
    "patato": "potato",
    "tamto": "tomato",
    "tamato": "tomato",
    "bittergroud": "bittergourd",
    "bitterguard": "bittergourd",
    "capsicuum": "capsicum",
}

# Nombres legibles para la interfaz.
DISPLAY_NAMES = {
    "apples": "Manzana",
    "banana": "Platano",
    "bittergourd": "Melon amargo",
    "capsicum": "Pimiento",
    "cucumber": "Pepino",
    "okra": "Okra",
    "oranges": "Naranja",
    "potato": "Papa",
    "tomato": "Tomate",
}

STATE_NAMES = {"fresh": "Fresco", "rotten": "Podrido"}


def normalize_folder(folder: str) -> tuple[str, str] | None:
    """Devuelve (fruta, estado) a partir del nombre de carpeta."""
    name = folder.strip().lower()
    match = re.match(r"^(fresh|rotten)[_\- ]?(.+)$", name)
    if not match:
        return None
    state, fruit = match.groups()
    fruit = CLASS_FIXES.get(fruit, fruit)
    if fruit not in DISPLAY_NAMES:
        return None
    return fruit, state


def file_digest(path: Path) -> str:
    digest = hashlib.md5()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def collect(dataset_root: Path) -> list[dict]:
    rows: list[dict] = []
    for split_dir in sorted(p for p in dataset_root.iterdir() if p.is_dir()):
        for class_dir in sorted(p for p in split_dir.iterdir() if p.is_dir()):
            parsed = normalize_folder(class_dir.name)
            if parsed is None:
                print(f"  [aviso] carpeta ignorada: {class_dir}")
                continue
            fruit, state = parsed
            for image in sorted(class_dir.iterdir()):
                if image.suffix.lower() not in IMAGE_EXTENSIONS:
                    continue
                rows.append(
                    {
                        "path": str(image.resolve()),
                        "label": f"{fruit}_{state}",
                        "fruit": fruit,
                        "state": state,
                        "original_split": split_dir.name,
                        "original_folder": class_dir.name,
                    }
                )
    return rows


def stratified_split(
    rows: list[dict], seed: int, train_ratio: float, val_ratio: float
) -> dict[str, list[dict]]:
    by_label: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        by_label[row["label"]].append(row)

    rng = random.Random(seed)
    splits: dict[str, list[dict]] = {"train": [], "val": [], "test": []}
    for label in sorted(by_label):
        items = by_label[label][:]
        rng.shuffle(items)
        n = len(items)
        n_train = int(n * train_ratio)
        n_val = int(n * val_ratio)
        # Garantiza al menos 1 muestra en val y test cuando la clase es pequena.
        n_val = max(1, n_val)
        n_train = min(n_train, n - n_val - 1)
        splits["train"].extend(items[:n_train])
        splits["val"].extend(items[n_train : n_train + n_val])
        splits["test"].extend(items[n_train + n_val :])
    return splits


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepara el manifest del dataset")
    parser.add_argument("--dataset", default="dataset", type=Path)
    parser.add_argument("--output", default="data", type=Path)
    parser.add_argument("--seed", default=42, type=int)
    parser.add_argument("--train-ratio", default=0.80, type=float)
    parser.add_argument("--val-ratio", default=0.10, type=float)
    args = parser.parse_args()

    dataset_root = args.dataset.resolve()
    if not dataset_root.is_dir():
        raise SystemExit(f"No existe el dataset: {dataset_root}")

    print(f"Escaneando {dataset_root} ...")
    rows = collect(dataset_root)
    print(f"  imagenes encontradas: {len(rows)}")

    print("Calculando hashes para eliminar duplicados ...")
    seen: dict[str, dict] = {}
    duplicates: Counter[str] = Counter()
    for row in rows:
        digest = file_digest(Path(row["path"]))
        row["md5"] = digest
        if digest in seen:
            duplicates[seen[digest]["label"]] += 1
            continue
        seen[digest] = row
    unique = list(seen.values())
    print(f"  unicas: {len(unique)}  |  duplicadas descartadas: {len(rows) - len(unique)}")

    splits = stratified_split(
        unique, args.seed, args.train_ratio, args.val_ratio
    )

    args.output.mkdir(parents=True, exist_ok=True)
    manifest = args.output / "manifest.csv"
    fieldnames = [
        "path",
        "label",
        "fruit",
        "state",
        "original_split",
        "original_folder",
        "md5",
        "split",
    ]
    with manifest.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for split_name, items in splits.items():
            for row in items:
                writer.writerow({**row, "split": split_name})

    labels = sorted({row["label"] for row in unique})
    labels_path = args.output / "labels.json"
    labels_path.write_text(
        json.dumps(
            [
                {
                    "label": label,
                    "fruit": label.split("_")[0],
                    "state": label.split("_")[1],
                    "display": (
                        f"{DISPLAY_NAMES[label.split('_')[0]]} "
                        f"{STATE_NAMES[label.split('_')[1]].lower()}"
                    ),
                }
                for label in labels
            ],
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    stats: dict[str, dict] = {}
    per_class: dict[str, dict[str, int]] = {label: {} for label in labels}
    for split_name, items in splits.items():
        counts = Counter(row["label"] for row in items)
        stats[split_name] = dict(sorted(counts.items()))
        for label in labels:
            per_class[label][split_name] = counts.get(label, 0)

    summary = {
        "dataset_root": str(dataset_root),
        "seed": args.seed,
        "total_raw": len(rows),
        "total_unique": len(unique),
        "duplicates_removed": len(rows) - len(unique),
        "num_classes": len(labels),
        "split_totals": {k: len(v) for k, v in splits.items()},
        "per_class": per_class,
        "duplicates_by_label": dict(duplicates),
    }
    (args.output / "dataset_stats.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print("\nResumen por split:")
    for split_name, total in summary["split_totals"].items():
        print(f"  {split_name:5} {total}")
    print(f"\nClases ({len(labels)}): {', '.join(labels)}")
    print(f"Manifest: {manifest}")
    print(f"Stats:    {args.output / 'dataset_stats.json'}")


if __name__ == "__main__":
    main()
