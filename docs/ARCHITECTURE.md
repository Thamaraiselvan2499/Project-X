# Architecture

## Customer flow

```
frontend/src/App.jsx (step state machine)
  LoginPage        -> POST /api/auth/login        (mobile+car number; auto-creates both)
  CarDetailsPage   -> PUT  /api/cars/{car_number}  (name/brand/variant/body_type — skipped for returning cars)
  CarViewerPage    -> three.js: rotatable schematic car (car3d/buildCar.js), click hotspots to
                      pick damaged parts (one hotspot per ml/configs/damage_classes.yaml part_labels entry)
  UploadPage       -> POST /api/reports              (once, creates the report)
                   -> POST /api/reports/{id}/items   (one call per selected part + its photo)
  ReportPage       <- GET-equivalent response from the last items call: itemized costs + total
```

## Detection pipeline (per uploaded photo)

```
┌─────────────┐   cvat_to_yolo.py    ┌───────────────┐   train.py      ┌──────────────┐
│ CVAT export │ ───────────────────▶ │ YOLO dataset  │ ───────────────▶│ best.pt      │
│ (xml/coco)  │                      │ (ml/data/yolo)│  (ultralytics)  │ (weights)    │
└─────────────┘                      └───────────────┘                 └──────┬───────┘
                                                                               │
                                                                               ▼
┌────────────────────────────────────────────────────────────────────────────────────┐
│ backend/app/services/detector.py (via services/analysis.py)                         │
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
│   one DamageItem row per detection, tagged with the customer-selected part          │
└──────────────────────────────────────┬───────────────────────────────────────────────┘
                                        ▼
                    SQLite (backend/app/db.py): User -> Car -> DamageReport -> DamageItem
                    (mobile_number is the User primary key, car_number the Car's —
                     see the login/no-OTP caveat in CONTRIBUTING.md)
```

`/api/annotate` (backend/app/routers/annotate.py) still exists as a standalone
single-image endpoint sharing the same `analyze_image_bytes` /
`build_quotation` code — useful for quick manual testing without going
through the full login/report flow.

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

## Why these choices (customer flow additions)

- **Part comes from the customer, not the model**: rather than requiring
  the detector to *also* localize which car part a detection is on (a
  second model output, or waiting for part-level CVAT annotation — see
  `ml/configs/damage_classes.yaml`'s `part_labels` comment), the customer
  points it out on the 3D viewer before uploading. This is simpler,
  works today with zero part-level training data, and is arguably more
  reliable than inferring part from a cropped damage photo anyway.
- **Schematic 3D car, not a licensed/photoreal model**: built from
  primitives in `car3d/buildCar.js` (boxes for body/cabin, cylinders for
  wheels, one hotspot sphere per part). Avoids a 3D-asset licensing/
  sourcing problem entirely — it only needs to be recognizable enough to
  rotate and point at, not photorealistic.
- **No OTP at login**: mobile number is the `User` primary key, car number
  the `Car`'s; a pair that hasn't been seen is auto-created rather than
  rejected. This is a deliberate scope cut for an internal pilot, not an
  oversight — see CONTRIBUTING.md before this goes anywhere customer-facing.
- **DamageReport groups multiple DamageItems**: solves what used to be
  listed here as an open gap (multi-photo submissions) — a report can have
  one item per (part, photo), added incrementally across several
  `POST /api/reports/{id}/items` calls, and the total is always recomputed
  from every item currently on the report.

## Known gaps / next decisions

- **Severity ground truth**: thresholds are calibrated against one small
  example dataset (see `ml/README.md`). Revisit as more real detections
  come in, ideally against the detected car's own bounding box rather
  than the whole frame (see the caveat in `damage_classes.yaml`).
- **Part-aware pricing**: a DamageItem already records which part the
  customer selected, but `quotation.py` still only prices by
  (damage_type, severity) — a dent on a bumper costs the same as a dent
  on a door. Extending `pricing.json` to key on (damage_type, part,
  severity) is a small, isolated change once real per-part costs exist.
- **Segmentation vs. detection**: if CVAT annotations include polygons,
  training with `--task segment` gives pixel-accurate area instead of a
  bounding-box approximation — worth it if severity accuracy from box
  area alone proves too coarse.
- **Real auth**: replacing the no-OTP login with actual phone
  verification (Firebase Phone Auth or an SMS vendor) before this is
  used outside an internal pilot.
