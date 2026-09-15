#!/usr/bin/env python3
"""Validate a trained model and run it through the same severity/quotation
logic the backend uses, so we can sanity-check end-to-end output on real
images before wiring the weights into the API.

    python ml/scripts/evaluate.py --data ml/data/yolo/data.yaml --weights ml/runs/train/weights/best.pt
    python ml/scripts/evaluate.py --weights ml/runs/train/weights/best.pt --image path/to/car.jpg
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ultralytics import YOLO

# Reuse the backend's severity/quotation logic instead of duplicating it.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))


def run_validation(weights: str, data: str) -> None:
    model = YOLO(weights)
    metrics = model.val(data=data)
    print(metrics)


def run_single_image(weights: str, image_path: str) -> None:
    from PIL import Image

    from app.models.schemas import BoundingBox, Detection
    from app.services.quotation import build_quotation
    from app.services.severity import estimate_severity

    model = YOLO(weights)
    image = Image.open(image_path).convert("RGB")
    width, height = image.size
    image_area = float(width * height)

    results = model.predict(image, verbose=False)
    names = results[0].names

    detections = []
    for result in results:
        boxes = result.boxes
        if boxes is None:
            continue
        for box, conf, cls_idx in zip(boxes.xyxy.tolist(), boxes.conf.tolist(), boxes.cls.tolist()):
            x_min, y_min, x_max, y_max = box
            area_ratio = ((x_max - x_min) * (y_max - y_min)) / image_area
            detections.append(
                Detection(
                    damage_type=names[int(cls_idx)],
                    confidence=float(conf),
                    bbox=BoundingBox(x_min=x_min, y_min=y_min, x_max=x_max, y_max=y_max),
                    area_ratio=area_ratio,
                    severity=estimate_severity(area_ratio),
                    needs_review=conf < 0.5,
                )
            )

    quotation = build_quotation(detections)
    print(f"{len(detections)} detection(s):")
    for d in detections:
        print(f"  - {d.damage_type} ({d.severity}, conf={d.confidence:.2f})")
    print(f"Quotation: {quotation.currency} {quotation.total:.2f} "
          f"(subtotal {quotation.subtotal:.2f} + service fee {quotation.service_fee:.2f})")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--weights", required=True)
    parser.add_argument("--data", help="data.yaml to run standard YOLO validation metrics against")
    parser.add_argument("--image", help="Single image to run through detection + severity + quotation")
    args = parser.parse_args()

    if args.data:
        run_validation(args.weights, args.data)
    if args.image:
        run_single_image(args.weights, args.image)
    if not args.data and not args.image:
        parser.error("pass --data and/or --image")


if __name__ == "__main__":
    main()
