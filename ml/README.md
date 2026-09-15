# ML pipeline

Converts CVAT annotations into a YOLO dataset, trains a detector, and
provides an evaluation script that runs the same severity + quotation
logic the backend uses.

## 1. Export from CVAT

In CVAT: Task/Project → Export dataset →
- **"CVAT for images 1.1"** (produces `annotations.xml`), or
- **"COCO 1.0"** (produces `instances_default.json`)

Either works. Also export/download the task's images if they aren't
already on disk locally.

Keep exports out of git — `ml/data/` is gitignored except for this README
and folder structure. Put exports under e.g. `ml/data/raw/<export-name>/`.

## 2. Convert to YOLO format

```bash
pip install -r ml/requirements.txt

python ml/scripts/cvat_to_yolo.py \
    --input ml/data/raw/my_export/annotations.xml \
    --images-dir ml/data/raw/my_export/images \
    --output ml/data/yolo \
    --classes ml/configs/damage_classes.yaml
```

This writes `ml/data/yolo/{images,labels}/{train,val}/` and a `data.yaml`
that `train.py` consumes. Labels in the CVAT export that aren't in
`ml/configs/damage_classes.yaml` are skipped with a warning — fix the
taxonomy file or the CVAT labels so they match, then re-run.

If any annotation is a polygon, the corresponding label is written in
YOLO-seg format; if it's only boxes, plain YOLO detection format is used.
Don't mix the two in one training run.

## 3. Train

```bash
python ml/scripts/train.py --data ml/data/yolo/data.yaml --task detect --epochs 100
```

Use `--task segment` (with a dataset converted from polygon annotations)
if we want per-pixel masks instead of boxes — better area estimates for
severity, heavier to train.

Weights land at `ml/runs/train/weights/best.pt`. Point the backend at them:

```bash
export MODEL_WEIGHTS_PATH=$(pwd)/ml/runs/train/weights/best.pt
```

Without this, the backend runs in **stub mode** — it returns deterministic
placeholder detections so the rest of the app (severity, quotation, API,
frontend) can be built and demoed before a model exists.

## 4. Evaluate

```bash
python ml/scripts/evaluate.py --weights ml/runs/train/weights/best.pt --data ml/data/yolo/data.yaml
python ml/scripts/evaluate.py --weights ml/runs/train/weights/best.pt --image some_car.jpg
```

The `--image` mode prints detections *and* the resulting quotation, using
the exact same `app.services.severity` / `app.services.quotation` code the
API calls — useful for sanity-checking real predictions end-to-end without
starting the server.

## Tuning severity & pricing

- `ml/configs/damage_classes.yaml` — class list and area-ratio thresholds
  for minor/moderate/severe. These are placeholders; revisit once we can
  look at real detection output.
- `backend/app/data/pricing.json` — repair cost per (damage type, severity).
  Also placeholder numbers — replace with real workshop quotes.
