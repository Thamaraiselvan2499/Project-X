# Architecture

## Pipeline

```
┌─────────────┐   cvat_to_yolo.py    ┌───────────────┐   train.py      ┌──────────────┐
│ CVAT export │ ───────────────────▶ │ YOLO dataset  │ ───────────────▶│ best.pt      │
│ (xml/coco)  │                      │ (ml/data/yolo)│  (ultralytics)  │ (weights)    │
└─────────────┘                      └───────────────┘                 └──────┬───────┘
                                                                               │
                                                                               ▼
┌────────────────────────────────────────────────────────────────────────────────────┐
│ backend/app/services/detector.py                                                    │
│   - loads best.pt if MODEL_WEIGHTS_PATH is set and exists                           │
│   - otherwise returns deterministic stub detections ("stub" mode)                   │
└──────────────────────────────────────┬───────────────────────────────────────────────┘
                                        ▼
┌────────────────────────────────────────────────────────────────────────────────────┐
│ backend/app/services/severity.py                                                    │
│   area_ratio = bbox_area / image_area  →  minor / moderate / severe                 │
│   (thresholds in ml/configs/damage_classes.yaml)                                    │
└──────────────────────────────────────┬───────────────────────────────────────────────┘
                                        ▼
┌────────────────────────────────────────────────────────────────────────────────────┐
│ backend/app/services/quotation.py                                                   │
│   (damage_type, severity) → cost, from backend/app/data/pricing.json                │
│   sums line items + a flat service fee → total                                      │
└──────────────────────────────────────┬───────────────────────────────────────────────┘
                                        ▼
                         FastAPI POST /api/annotate (backend/app/routers/annotate.py)
                                        │  JSON: detections[], quotation, model_mode
                                        ▼
                         React frontend (frontend/src/App.jsx)
                           - AnnotatedImage.jsx: canvas overlay, boxes colored by severity
                           - QuotationTable.jsx: line items + total, low-confidence flags
```

## Why these choices

- **Detection, not pure classification**: a quotation needs to know *how
  many* damage instances there are and *how big* each one is, not just
  "this car has a dent somewhere". Bounding boxes give us both a location
  (useful for the UI overlay) and an area (used as the severity proxy).
- **Area ratio as the severity proxy, not a learned severity classifier**:
  we don't have severity labels yet. Area-of-frame is a simple, inspectable
  starting point that gets the pipeline end-to-end; it's isolated behind
  `estimate_severity()` so it can be replaced by a trained
  regressor/classifier later without touching detector or quotation code.
- **Stub detector mode**: lets backend, frontend, and API-contract work
  proceed in parallel with training, instead of blocking everyone on a
  finished model.
- **Pricing as a JSON config, not a database or hardcoded table**: repair
  costs are business data that changes independent of code — a
  non-engineer (or a script) can edit `pricing.json` without touching
  Python. If per-region or per-workshop pricing is needed later, this is
  the file to extend into a lookup keyed by more than damage type/severity.
- **`ml/configs/damage_classes.yaml` as the single taxonomy source**: class
  names have to stay in sync across CVAT, the trained model, and the
  pricing table. Keeping one canonical file (rather than duplicating the
  list in three places) is what makes `cvat_to_yolo.py` able to flag
  mismatches instead of silently mislabeling data.

## Known gaps / next decisions

- **Severity ground truth**: current thresholds are guesses. Once there's
  a batch of real detections, look at the area-ratio distribution and/or
  get a few engineers to manually severity-label a sample to calibrate.
- **Part localization**: pricing is currently damage-type + severity only,
  not damage-type + part (a scratch on a bumper vs. a door may cost
  differently in practice). Extending the taxonomy to include part would
  mean either a second model output or compound classes
  (e.g. `bumper_scratch`).
- **Segmentation vs. detection**: if CVAT annotations include polygons,
  training with `--task segment` gives pixel-accurate area instead of a
  bounding-box approximation — worth it if severity accuracy from box
  area alone proves too coarse.
- **Multi-photo submissions**: real insurance/workshop estimates usually
  come from several angles of the same vehicle; the current API is
  single-image. Aggregating multiple `/api/annotate` calls into one
  quotation (and deduplicating the same damage seen from two angles) is
  unsolved.
