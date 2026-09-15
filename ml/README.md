# ML pipeline

Converts CVAT annotations into a YOLO dataset, trains a detector, and
provides an evaluation script that runs the same severity + quotation
logic the backend uses.

## Try it now with the checked-in example

`ml/data/examples/maruti_suzuki_suv_brezza/` is a real (small) CVAT export
committed to the repo — 9 images from the `Maruti_Brezza_SUV_Damage` CVAT
project — so anyone can run the whole pipeline immediately without needing
CVAT access first:

```bash
pip install -r ml/requirements.txt

python ml/scripts/cvat_to_yolo.py \
    --input ml/data/examples/maruti_suzuki_suv_brezza/annotations.xml \
    --images-dir ml/data/examples/maruti_suzuki_suv_brezza/images \
    --output ml/data/yolo \
    --classes ml/configs/damage_classes.yaml

python ml/scripts/train.py --data ml/data/yolo/data.yaml --epochs 3 --imgsz 320
```

9 images trains nothing that generalizes — this is a pipeline check, not a
real model. It's enough to confirm conversion, training, and the backend's
`MODEL_WEIGHTS_PATH` integration all work end-to-end before waiting on a
real dataset.

### Getting a management-demo-quality result from these 9 images

Running longer with more epochs makes the model memorize this specific
set of images well enough to demo convincingly — it still won't detect
damage in a *new* photo reliably, but it correctly boxes and quotes the
sample images:

```bash
python ml/scripts/train.py --data ml/data/yolo/data.yaml --epochs 120 --imgsz 480 --batch 4
```

Tested against all 9 sample images afterward (`MODEL_WEIGHTS_PATH` pointed
at the resulting `ml/runs/train/weights/best.pt`, calling `/api/annotate`
for each): 5 of 9 produce a confident detection, all classified `dent`
(the other 11 classes have too few examples each to be learned
reliably from 8 training images) with a quotation matching that instance's
size in frame. For a live demo, use these — a random pick from the folder
has good odds of landing on one of the 4 with no detection:

| Image | Confidence | Severity | Quote |
|---|---|---|---|
| `Back full part deformation.png` | 0.96 | severe | ₹8,300 |
| `Front part dent , broken part damage.png` | 0.98 | moderate | ₹3,800 |
| `front part full deformation.png` | 0.86 | severe | ₹8,300 |
| `front part full deformation 09-09-2026 12_44_15_197.png` | 0.52 | minor | ₹1,800 |

The last one is the only "minor" result — worth including if you want to
show all three severity levels rather than just severe/moderate.

## 1. Export from CVAT

In CVAT: Task/Project → Export dataset →
- **"CVAT for images 1.1"** (produces `annotations.xml`), or
- **"COCO 1.0"** (produces `instances_default.json`)

Either works. Also export/download the task's images if they aren't
already on disk locally.

For a real (large) export, put it under `ml/data/raw/<brand-or-task-name>/`
— that path is gitignored, unlike `ml/data/examples/`. Only small,
deliberately-committed reference datasets belong under `examples/`.

## 2. Convert to YOLO format

```bash
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

**Real CVAT exports mix box and polygon shapes across images** (the
checked-in example does: 6 of 9 images are polygons, 3 are plain boxes) —
YOLO can't train on a label directory that mixes the two formats. Every
object is normalized to one format via `--label-format` (default `box`,
which derives a bounding box from any polygon; use `polygon` to instead
synthesize a rectangular mask for any plain box, for `--task segment`).

**Adding another brand?** Run this script again with the same `--output`
— each run appends into `images/{train,val}` and `labels/{train,val}`
rather than clearing them, and output filenames are prefixed with a
dataset name (auto-derived from `--images-dir`'s parent folder, or set
`--dataset-name`) so two brands' images with the same filename (e.g. both
having a "front side damage.png") don't collide.

## 3. Train

```bash
python ml/scripts/train.py --data ml/data/yolo/data.yaml --task detect --epochs 100
```

Use `--task segment` (with a dataset converted with `--label-format
polygon`) if we want per-pixel masks instead of boxes — better area
estimates for severity, heavier to train.

Weights land at `ml/runs/<name>/weights/best.pt` (`ml/runs/train/...` by
default). Point the backend at them:

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

- `ml/configs/damage_classes.yaml` — the 12-class damage taxonomy (sourced
  from the real CVAT project, not guessed), the 20-label part taxonomy
  (defined in CVAT but not yet annotated anywhere — see the comment in that
  file), and the area-ratio thresholds for minor/moderate/severe. The
  thresholds are placeholders; revisit once we can look at real detection
  output.
- `backend/app/data/pricing.json` — repair cost per (damage type, severity).
  Also placeholder numbers — replace with real workshop quotes.
