"""Entrenamiento con transfer learning (MobileNetV3-Small, ImageNet).

Genera en `ml/artifacts/`:
  - model.onnx / model.ts  -> modelo exportado para inferencia
  - labels.json            -> orden exacto de las clases
  - model_meta.json        -> tamano de entrada y normalizacion
  - metrics.json           -> historial de epochs + reporte final
  - curves.png             -> curvas de loss/accuracy
  - confusion_matrix.png   -> matriz de confusion normalizada
  - classification_report.txt

Uso:
    py -3 ml/train.py --epochs 8 --batch-size 64
"""

from __future__ import annotations

import argparse
import copy
import csv
import json
import random
import time
from collections import Counter
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset, WeightedRandomSampler
from torchvision import models, transforms
from PIL import Image

IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]


class ManifestDataset(Dataset):
    def __init__(self, rows: list[dict], label_to_index: dict[str, int], transform):
        self.rows = rows
        self.label_to_index = label_to_index
        self.transform = transform

    def __len__(self) -> int:
        return len(self.rows)

    def __getitem__(self, index: int):
        row = self.rows[index]
        with Image.open(row["path"]) as image:
            image = image.convert("RGB")
            tensor = self.transform(image)
        return tensor, self.label_to_index[row["label"]]


def load_manifest(manifest_path: Path) -> list[dict]:
    with manifest_path.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _group_by_label(rows: list[dict]) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = {}
    for row in rows:
        grouped.setdefault(row["label"], []).append(row)
    return grouped


def build_transforms(image_size: int):
    train_tf = transforms.Compose(
        [
            transforms.RandomResizedCrop(image_size, scale=(0.60, 1.0), ratio=(0.8, 1.25)),
            transforms.RandomHorizontalFlip(),
            transforms.RandomRotation(15),
            transforms.ColorJitter(brightness=0.25, contrast=0.25, saturation=0.25, hue=0.05),
            transforms.ToTensor(),
            transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
        ]
    )
    eval_tf = transforms.Compose(
        [
            transforms.Resize(int(image_size * 1.14)),
            transforms.CenterCrop(image_size),
            transforms.ToTensor(),
            transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
        ]
    )
    return train_tf, eval_tf


def build_model(num_classes: int) -> nn.Module:
    model = models.mobilenet_v3_small(weights=models.MobileNet_V3_Small_Weights.IMAGENET1K_V1)
    in_features = model.classifier[3].in_features
    model.classifier[3] = nn.Linear(in_features, num_classes)
    return model


def select_device(requested: str, model: nn.Module, image_size: int) -> torch.device:
    """Elige GPU si funciona de verdad; si el backend falla, cae a CPU.

    En Windows con ROCm hay builds de MIOpen que no compilan el kernel de
    BatchNorm (hiprtc no encuentra los headers de C++). Se prueba un paso de
    forward/backward con datos aleatorios y, si falla, se entrena en CPU.
    """
    if requested == "cpu" or not torch.cuda.is_available():
        print("Dispositivo: cpu")
        return torch.device("cpu")

    device = torch.device("cuda")
    snapshot = copy.deepcopy(model.state_dict())
    try:
        torch.backends.miopen.enabled = False
    except Exception:
        pass
    try:
        model.to(device).train()
        dummy = torch.randn(2, 3, image_size, image_size, device=device)
        loss = model(dummy).sum()
        loss.backward()
        model.zero_grad(set_to_none=True)
        torch.cuda.synchronize()
        model.load_state_dict(snapshot)
        print(f"Dispositivo: cuda ({torch.cuda.get_device_name(0)})")
        return device
    except Exception as exc:
        print(f"[aviso] la GPU fallo en la prueba inicial ({type(exc).__name__}: {exc}).")
        print("        Se usara CPU. Para forzar GPU revisa el runtime de ROCm/MIOpen.")
        model.load_state_dict(snapshot)
        model.cpu()
        torch.cuda.empty_cache()
        return torch.device("cpu")


@torch.no_grad()
def evaluate(model: nn.Module, loader: DataLoader, criterion, device: torch.device):
    model.eval()
    total_loss = 0.0
    all_preds: list[int] = []
    all_targets: list[int] = []
    for images, targets in loader:
        images, targets = images.to(device), targets.to(device)
        logits = model(images)
        total_loss += criterion(logits, targets).item() * targets.size(0)
        all_preds.extend(logits.argmax(1).cpu().tolist())
        all_targets.extend(targets.cpu().tolist())
    preds = np.array(all_preds)
    targets = np.array(all_targets)
    accuracy = float((preds == targets).mean()) if len(targets) else 0.0
    return total_loss / max(1, len(targets)), accuracy, preds, targets


def save_curves(history: list[dict], output_dir: Path) -> None:
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception as exc:  # pragma: no cover
        print(f"[aviso] no se pudieron dibujar curvas: {exc}")
        return

    epochs = [h["epoch"] for h in history]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5))
    ax1.plot(epochs, [h["train_loss"] for h in history], label="train")
    ax1.plot(epochs, [h["val_loss"] for h in history], label="val")
    ax1.set_title("Pérdida (CrossEntropy)")
    ax1.set_xlabel("epoch")
    ax1.legend()
    ax1.grid(alpha=0.3)

    ax2.plot(epochs, [h["train_acc"] for h in history], label="train")
    ax2.plot(epochs, [h["val_acc"] for h in history], label="val")
    ax2.set_title("Exactitud")
    ax2.set_xlabel("epoch")
    ax2.set_ylim(0, 1.02)
    ax2.legend()
    ax2.grid(alpha=0.3)

    fig.tight_layout()
    fig.savefig(output_dir / "curves.png", dpi=140)
    plt.close(fig)


def save_confusion_matrix(
    preds: np.ndarray, targets: np.ndarray, labels: list[str], output_dir: Path
) -> dict:
    from sklearn.metrics import classification_report, confusion_matrix

    matrix = confusion_matrix(targets, preds, labels=list(range(len(labels))))
    normalized = matrix.astype(float) / np.maximum(1, matrix.sum(axis=1, keepdims=True))

    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(12, 10))
        image = ax.imshow(normalized, cmap="Blues", vmin=0, vmax=1)
        ax.set_xticks(range(len(labels)))
        ax.set_yticks(range(len(labels)))
        ax.set_xticklabels(labels, rotation=90, fontsize=7)
        ax.set_yticklabels(labels, fontsize=7)
        ax.set_xlabel("Predicción")
        ax.set_ylabel("Real")
        ax.set_title("Matriz de confusión normalizada")
        for i in range(len(labels)):
            for j in range(len(labels)):
                if normalized[i, j] >= 0.01:
                    ax.text(
                        j,
                        i,
                        f"{normalized[i, j]:.2f}",
                        ha="center",
                        va="center",
                        fontsize=5,
                        color="white" if normalized[i, j] > 0.55 else "black",
                    )
        fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04)
        fig.tight_layout()
        fig.savefig(output_dir / "confusion_matrix.png", dpi=140)
        plt.close(fig)
    except Exception as exc:  # pragma: no cover
        print(f"[aviso] no se pudo dibujar la matriz: {exc}")

    report = classification_report(
        targets, preds, labels=list(range(len(labels))), target_names=labels, digits=4, zero_division=0
    )
    (output_dir / "classification_report.txt").write_text(report, encoding="utf-8")
    print("\n" + report)
    return {"confusion_matrix": matrix.tolist(), "report": report}


def export_models(model: nn.Module, image_size: int, output_dir: Path) -> dict[str, str]:
    model = model.cpu().eval()
    dummy = torch.randn(1, 3, image_size, image_size)
    exported: dict[str, str] = {}

    try:
        onnx_path = output_dir / "model.onnx"
        torch.onnx.export(
            model,
            dummy,
            str(onnx_path),
            input_names=["input"],
            output_names=["logits"],
            opset_version=17,
            do_constant_folding=True,
            dynamo=False,
        )
        exported["onnx"] = onnx_path.name
        print(f"[ok] ONNX exportado: {onnx_path} ({onnx_path.stat().st_size / 1e6:.1f} MB)")
    except Exception as exc:
        print(f"[aviso] export ONNX fallo ({exc}); se usara TorchScript")

    try:
        ts_path = output_dir / "model.ts"
        torch.jit.trace(model, dummy, strict=False).save(str(ts_path))
        exported["torchscript"] = ts_path.name
    except Exception as exc:
        print(f"[aviso] export TorchScript fallo: {exc}")

    return exported


def main() -> None:
    parser = argparse.ArgumentParser(description="Fine-tuning MobileNetV3-Small")
    parser.add_argument("--manifest", default="data/manifest.csv", type=Path)
    parser.add_argument("--labels", default="data/labels.json", type=Path)
    parser.add_argument("--output", default="ml/artifacts", type=Path)
    parser.add_argument("--epochs", default=8, type=int)
    parser.add_argument("--batch-size", default=64, type=int)
    parser.add_argument("--lr", default=3e-4, type=float)
    parser.add_argument("--weight-decay", default=1e-4, type=float)
    parser.add_argument("--image-size", default=224, type=int)
    parser.add_argument("--workers", default=4, type=int)
    parser.add_argument("--seed", default=42, type=int)
    parser.add_argument("--patience", default=3, type=int)
    parser.add_argument("--device", default="auto", choices=["auto", "cuda", "cpu"])
    parser.add_argument(
        "--max-per-class",
        default=0,
        type=int,
        help="Limita las imagenes de entrenamiento por clase (0 = sin limite).",
    )
    args = parser.parse_args()

    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    torch.cuda.manual_seed_all(args.seed)

    rows = load_manifest(args.manifest)
    label_defs = json.loads(args.labels.read_text(encoding="utf-8"))
    labels = [item["label"] for item in label_defs]
    label_to_index = {label: index for index, label in enumerate(labels)}
    num_classes = len(labels)

    grouped = {name: [row for row in rows if row["split"] == name] for name in ("train", "val", "test")}

    if args.max_per_class > 0:
        rng = random.Random(args.seed)
        limited: dict[str, list[dict]] = {}
        for label, items in _group_by_label(grouped["train"]).items():
            limited[label] = items if len(items) <= args.max_per_class else rng.sample(items, args.max_per_class)
        grouped["train"] = [row for items in limited.values() for row in items]
        print(f"[modo rapido] entrenamiento limitado a {args.max_per_class} imagenes por clase")

    for name, items in grouped.items():
        print(f"{name:5} {len(items):6} imagenes")

    model = build_model(num_classes)
    device = select_device(args.device, model, args.image_size)
    model.to(device)
    if device.type == "cpu":
        torch.set_num_threads(max(1, (torch.get_num_threads() or 4)))
    pin_memory = device.type == "cuda"

    train_tf, eval_tf = build_transforms(args.image_size)
    train_ds = ManifestDataset(grouped["train"], label_to_index, train_tf)
    val_ds = ManifestDataset(grouped["val"], label_to_index, eval_tf)
    test_ds = ManifestDataset(grouped["test"], label_to_index, eval_tf)

    # Balanceo de clases: las clases con menos imagenes se muestrean mas.
    class_counts = Counter(row["label"] for row in grouped["train"])
    sample_weights = [1.0 / class_counts[row["label"]] for row in grouped["train"]]
    sampler = WeightedRandomSampler(sample_weights, num_samples=len(sample_weights), replacement=True)

    train_loader = DataLoader(
        train_ds, batch_size=args.batch_size, sampler=sampler,
        num_workers=args.workers, pin_memory=pin_memory, persistent_workers=args.workers > 0,
    )
    val_loader = DataLoader(
        val_ds, batch_size=args.batch_size, shuffle=False,
        num_workers=args.workers, pin_memory=pin_memory, persistent_workers=args.workers > 0,
    )
    test_loader = DataLoader(
        test_ds, batch_size=args.batch_size, shuffle=False,
        num_workers=args.workers, pin_memory=pin_memory, persistent_workers=args.workers > 0,
    )

    criterion = nn.CrossEntropyLoss(label_smoothing=0.1)

    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs)
    scaler = torch.amp.GradScaler("cuda", enabled=device.type == "cuda")

    args.output.mkdir(parents=True, exist_ok=True)
    history: list[dict] = []
    best_acc = 0.0
    best_epoch = 0
    epochs_without_improvement = 0

    for epoch in range(1, args.epochs + 1):
        model.train()
        running_loss = 0.0
        correct = 0
        seen = 0
        started = time.time()

        for images, targets in train_loader:
            images, targets = images.to(device, non_blocking=True), targets.to(device, non_blocking=True)
            optimizer.zero_grad(set_to_none=True)
            with torch.amp.autocast("cuda", enabled=device.type == "cuda"):
                logits = model(images)
                loss = criterion(logits, targets)
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()

            running_loss += loss.item() * targets.size(0)
            correct += (logits.argmax(1) == targets).sum().item()
            seen += targets.size(0)

        train_loss = running_loss / max(1, seen)
        train_acc = correct / max(1, seen)
        val_loss, val_acc, _, _ = evaluate(model, val_loader, criterion, device)
        scheduler.step()

        elapsed = time.time() - started
        history.append(
            {
                "epoch": epoch,
                "train_loss": round(train_loss, 5),
                "train_acc": round(train_acc, 5),
                "val_loss": round(val_loss, 5),
                "val_acc": round(val_acc, 5),
                "lr": optimizer.param_groups[0]["lr"],
                "seconds": round(elapsed, 2),
            }
        )
        print(
            f"epoch {epoch:2}/{args.epochs} | train loss {train_loss:.4f} acc {train_acc:.4f} "
            f"| val loss {val_loss:.4f} acc {val_acc:.4f} | {elapsed:.1f}s"
        )

        if val_acc > best_acc:
            best_acc = val_acc
            best_epoch = epoch
            epochs_without_improvement = 0
            torch.save(
                {"state_dict": model.state_dict(), "labels": labels, "image_size": args.image_size},
                args.output / "model.pt",
            )
            print(f"  -> nuevo mejor modelo (val_acc {best_acc:.4f})")
        else:
            epochs_without_improvement += 1
            if epochs_without_improvement >= args.patience:
                print(f"  -> early stopping en epoch {epoch}")
                break

    checkpoint = torch.load(args.output / "model.pt", map_location=device)
    model.load_state_dict(checkpoint["state_dict"])

    test_loss, test_acc, preds, targets = evaluate(model, test_loader, criterion, device)
    print(f"\nTEST loss {test_loss:.4f} | accuracy {test_acc:.4f}")

    details = save_confusion_matrix(preds, targets, labels, args.output)
    save_curves(history, args.output)

    artifacts = export_models(model, args.image_size, args.output)

    (args.output / "labels.json").write_text(
        json.dumps(
            [{**item, "index": index} for index, item in enumerate(label_defs)],
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (args.output / "model_meta.json").write_text(
        json.dumps(
            {
                "architecture": "mobilenet_v3_small",
                "image_size": args.image_size,
                "mean": IMAGENET_MEAN,
                "std": IMAGENET_STD,
                "num_classes": len(labels),
                "artifacts": artifacts,
                "trained_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (args.output / "metrics.json").write_text(
        json.dumps(
            {
                "history": history,
                "best_epoch": best_epoch,
                "best_val_acc": best_acc,
                "test_loss": test_loss,
                "test_acc": test_acc,
                "test_samples": int(len(targets)),
                "confusion_matrix": details["confusion_matrix"],
                "labels": labels,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print(f"\nArtefactos en {args.output.resolve()}")


if __name__ == "__main__":
    main()
