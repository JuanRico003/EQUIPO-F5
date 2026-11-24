"""Tests del pipeline de datos (sin dependencias de GPU)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ml.prepare_data import normalize_folder, stratified_split


def test_normalize_folder_corrige_typos():
    assert normalize_folder("freshpatato") == ("potato", "fresh")
    assert normalize_folder("rottenpatato") == ("potato", "rotten")
    assert normalize_folder("freshtamto") == ("tomato", "fresh")
    assert normalize_folder("rottentamto") == ("tomato", "rotten")
    assert normalize_folder("freshbittergroud") == ("bittergourd", "fresh")


def test_normalize_folder_clases_validas():
    assert normalize_folder("freshapples") == ("apples", "fresh")
    assert normalize_folder("rottenokra") == ("okra", "rotten")
    assert normalize_folder("Fresh-Capsicum") == ("capsicum", "fresh")


def test_normalize_folder_ignora_desconocidas():
    assert normalize_folder("otra_cosa") is None
    assert normalize_folder("freshdesconocida") is None


def test_stratified_split_respeta_proporciones_y_no_pierde_datos():
    rows = []
    for label in ("apples_fresh", "apples_rotten"):
        rows.extend({"label": label, "path": f"{label}_{index}.png"} for index in range(100))

    splits = stratified_split(rows, seed=7, train_ratio=0.8, val_ratio=0.1)
    assert sum(len(items) for items in splits.values()) == 200
    assert len(splits["train"]) == 160
    assert len(splits["val"]) == 20
    assert len(splits["test"]) == 20


def test_stratified_split_clases_pequenas_tienen_val_y_test():
    rows = [{"label": "okra_fresh", "path": f"{index}.png"} for index in range(3)]
    splits = stratified_split(rows, seed=1, train_ratio=0.8, val_ratio=0.1)
    assert len(splits["val"]) >= 1
    assert len(splits["test"]) >= 1
    assert len(splits["train"]) >= 1
