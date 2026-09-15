#!/usr/bin/env python3
"""Train a YOLOv8 detection or segmentation model on the converted dataset.

Run ml/scripts/cvat_to_yolo.py first to produce data.yaml. Example:

    python ml/scripts/train.py \\
        --data ml/data/yolo/data.yaml \\
        --task detect \\
        --epochs 100 \\
        --model yolov8n.pt

The best weights land at <project>/<name>/weights/best.pt — point the
backend at it via the MODEL_WEIGHTS_PATH env var, or copy it to
ml/runs/weights/best.pt (the backend's default lookup path).
"""
from __future__ import annotations

import argparse

from ultralytics import YOLO


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data", required=True, help="Path to data.yaml produced by cvat_to_yolo.py")
    parser.add_argument("--task", choices=["detect", "segment"], default="detect")
    parser.add_argument(
        "--model",
        default=None,
        help="Base checkpoint to fine-tune from, e.g. yolov8n.pt / yolov8n-seg.pt "
        "(default: yolov8n.pt for detect, yolov8n-seg.pt for segment)",
    )
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--batch", type=int, default=16)
    parser.add_argument("--project", default="ml/runs", help="Output directory for training runs")
    parser.add_argument("--name", default="train")
    args = parser.parse_args()

    base_model = args.model or ("yolov8n-seg.pt" if args.task == "segment" else "yolov8n.pt")

    model = YOLO(base_model)
    model.train(
        data=args.data,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        project=args.project,
        name=args.name,
    )


if __name__ == "__main__":
    main()
