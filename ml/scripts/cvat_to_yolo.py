#!/usr/bin/env python3
"""Convert a CVAT export into a YOLO-format training dataset.

Supports the two most common CVAT export formats:
  - "CVAT for images 1.1" (an annotations.xml with <image>/<box>/<polygon> tags)
  - "COCO 1.0" (an instances_*.json file)

Boxes become YOLO detection labels (`class xc yc w h`, normalized).
Polygons become YOLO-seg labels (`class x1 y1 x2 y2 ... xn yn`, normalized).
An image with only boxes still trains a detection model; if *any* image in
the export has polygons, prefer training with `ml/scripts/train.py --task
segment` since a mix of formats in one label file is not valid YOLO.

Usage:
    python ml/scripts/cvat_to_yolo.py \\
        --input path/to/annotations.xml \\
        --images-dir path/to/images \\
        --output ml/data/yolo \\
        --classes ml/configs/damage_classes.yaml

    python ml/scripts/cvat_to_yolo.py \\
        --input path/to/instances_default.json \\
        --images-dir path/to/images \\
        --format coco \\
        --output ml/data/yolo
"""
from __future__ import annotations

import argparse
import json
import random
import shutil
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class ObjectAnnotation:
    label: str
    # Either bbox (x_min, y_min, x_max, y_max) in pixels, or polygon points.
    bbox: tuple[float, float, float, float] | None = None
    polygon: list[tuple[float, float]] | None = None


@dataclass
class ImageAnnotation:
    filename: str
    width: int
    height: int
    objects: list[ObjectAnnotation] = field(default_factory=list)


def normalize_label(label: str) -> str:
    return label.strip().lower().replace(" ", "_").replace("-", "_")


def parse_cvat_xml(xml_path: Path) -> list[ImageAnnotation]:
    tree = ET.parse(xml_path)
    root = tree.getroot()
    images: list[ImageAnnotation] = []

    for image_el in root.findall("image"):
        filename = image_el.get("name")
        width = int(float(image_el.get("width")))
        height = int(float(image_el.get("height")))
        image_ann = ImageAnnotation(filename=filename, width=width, height=height)

        for box_el in image_el.findall("box"):
            label = normalize_label(box_el.get("label"))
            bbox = (
                float(box_el.get("xtl")),
                float(box_el.get("ytl")),
                float(box_el.get("xbr")),
                float(box_el.get("ybr")),
            )
            image_ann.objects.append(ObjectAnnotation(label=label, bbox=bbox))

        for poly_el in image_el.findall("polygon"):
            label = normalize_label(poly_el.get("label"))
            points_raw = poly_el.get("points")  # "x1,y1;x2,y2;..."
            points = [tuple(map(float, p.split(","))) for p in points_raw.split(";")]
            image_ann.objects.append(ObjectAnnotation(label=label, polygon=points))

        images.append(image_ann)

    return images


def parse_coco(json_path: Path) -> list[ImageAnnotation]:
    with open(json_path) as f:
        data = json.load(f)

    categories = {cat["id"]: normalize_label(cat["name"]) for cat in data["categories"]}
    images_by_id = {
        img["id"]: ImageAnnotation(filename=img["file_name"], width=img["width"], height=img["height"])
        for img in data["images"]
    }

    for ann in data["annotations"]:
        image_ann = images_by_id.get(ann["image_id"])
        if image_ann is None:
            continue
        label = categories.get(ann["category_id"], "unknown")

        x, y, w, h = ann["bbox"]
        obj = ObjectAnnotation(label=label, bbox=(x, y, x + w, y + h))

        segmentation = ann.get("segmentation")
        if segmentation and isinstance(segmentation, list) and len(segmentation) > 0:
            flat = segmentation[0]
            obj.polygon = list(zip(flat[0::2], flat[1::2]))

        image_ann.objects.append(obj)

    return list(images_by_id.values())


def to_yolo_lines(image_ann: ImageAnnotation, class_index: dict[str, int], unknown_labels: set[str]) -> list[str]:
    lines = []
    w, h = image_ann.width, image_ann.height
    for obj in image_ann.objects:
        if obj.label not in class_index:
            unknown_labels.add(obj.label)
            continue
        idx = class_index[obj.label]

        if obj.polygon:
            coords = []
            for px, py in obj.polygon:
                coords.append(f"{px / w:.6f}")
                coords.append(f"{py / h:.6f}")
            lines.append(f"{idx} " + " ".join(coords))
        elif obj.bbox:
            x_min, y_min, x_max, y_max = obj.bbox
            xc = ((x_min + x_max) / 2) / w
            yc = ((y_min + y_max) / 2) / h
            bw = (x_max - x_min) / w
            bh = (y_max - y_min) / h
            lines.append(f"{idx} {xc:.6f} {yc:.6f} {bw:.6f} {bh:.6f}")
    return lines


def build_dataset(
    images: list[ImageAnnotation],
    images_dir: Path,
    output_dir: Path,
    classes: list[str],
    val_split: float,
    seed: int,
) -> None:
    class_index = {normalize_label(c): i for i, c in enumerate(classes)}
    unknown_labels: set[str] = set()

    # Only images that actually resolve to a file are usable.
    resolvable = []
    for img in images:
        src = images_dir / img.filename
        if src.exists():
            resolvable.append(img)
        else:
            print(f"warning: image not found, skipping: {src}", file=sys.stderr)

    random.Random(seed).shuffle(resolvable)
    n_val = max(1, int(len(resolvable) * val_split)) if resolvable else 0
    val_set = set(id(img) for img in resolvable[:n_val])

    for split in ("train", "val"):
        (output_dir / "images" / split).mkdir(parents=True, exist_ok=True)
        (output_dir / "labels" / split).mkdir(parents=True, exist_ok=True)

    written = 0
    for img in resolvable:
        split = "val" if id(img) in val_set else "train"
        lines = to_yolo_lines(img, class_index, unknown_labels)

        src = images_dir / img.filename
        dst_image = output_dir / "images" / split / Path(img.filename).name
        shutil.copyfile(src, dst_image)

        label_path = output_dir / "labels" / split / (Path(img.filename).stem + ".txt")
        label_path.write_text("\n".join(lines) + ("\n" if lines else ""))
        written += 1

    data_yaml = {
        "path": str(output_dir.resolve()),
        "train": "images/train",
        "val": "images/val",
        "names": {i: c for i, c in enumerate(classes)},
    }
    with open(output_dir / "data.yaml", "w") as f:
        yaml.safe_dump(data_yaml, f, sort_keys=False)

    print(f"Wrote {written} images ({len(resolvable) - n_val} train / {n_val} val) to {output_dir}")
    if unknown_labels:
        print(
            f"warning: {len(unknown_labels)} label(s) in the export are not in the configured "
            f"taxonomy and were skipped: {sorted(unknown_labels)}",
            file=sys.stderr,
        )


def detect_format(input_path: Path) -> str:
    if input_path.suffix.lower() == ".json":
        return "coco"
    return "cvat_xml"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--input", required=True, type=Path, help="CVAT annotations.xml or COCO instances_*.json")
    parser.add_argument("--images-dir", required=True, type=Path, help="Directory containing the source images")
    parser.add_argument("--output", required=True, type=Path, help="Output YOLO dataset directory")
    parser.add_argument(
        "--classes",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "configs" / "damage_classes.yaml",
        help="YAML file with the class list (default: ml/configs/damage_classes.yaml)",
    )
    parser.add_argument("--format", choices=["auto", "cvat_xml", "coco"], default="auto")
    parser.add_argument("--val-split", type=float, default=0.15)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    fmt = args.format if args.format != "auto" else detect_format(args.input)
    images = parse_cvat_xml(args.input) if fmt == "cvat_xml" else parse_coco(args.input)

    with open(args.classes) as f:
        classes = yaml.safe_load(f)["classes"]

    build_dataset(images, args.images_dir, args.output, classes, args.val_split, args.seed)


if __name__ == "__main__":
    main()
