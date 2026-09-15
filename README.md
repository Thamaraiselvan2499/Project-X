# Project X — Car Damage Annotation & Repair Estimator

Detects damage in a photo of a car, estimates severity, and returns an
instant repair-cost quotation.

**Team:** Thamaraiselvan (repo owner), Rajana, Ranjini — AI Engineers.

## Status

- ✅ Damage annotation of car images (by damage type) — done in CVAT.
- ✅ Backend API + quotation logic scaffolded and tested (runs in demo/stub
  mode until a trained model is dropped in).
- ✅ CVAT export → YOLO dataset converter.
- ✅ Frontend upload + annotated-image + quotation UI.
- ⏳ Not yet done: pulling the CVAT export into this repo, training the
  detector, tuning severity thresholds and repair pricing against real data.

## How it works

```
CVAT export (annotations.xml / COCO json)
        │  ml/scripts/cvat_to_yolo.py
        ▼
YOLO dataset (ml/data/yolo/)
        │  ml/scripts/train.py  (ultralytics YOLOv8)
        ▼
Trained weights (best.pt)
        │  backend/app/services/detector.py
        ▼
Detections (damage type, bbox, confidence)
        │  backend/app/services/severity.py   (area ratio -> minor/moderate/severe)
        │  backend/app/services/quotation.py  (severity -> cost, from pricing.json)
        ▼
FastAPI /api/annotate  →  React frontend (bbox overlay + quotation table)
```

See `docs/ARCHITECTURE.md` for more detail.

## Repo layout

```
backend/    FastAPI service: detection, severity, quotation, HTTP API
ml/         CVAT->YOLO conversion, training, evaluation scripts
frontend/   React (Vite) upload + results UI
docs/       Architecture notes
```

## Quickstart

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Without trained model weights, `/api/annotate` runs in **stub mode**:
it returns fixed placeholder detections so the whole pipeline (severity,
quotation, frontend) is testable before training finishes. Once you have
weights (see `ml/README.md`):

```bash
export MODEL_WEIGHTS_PATH=/path/to/best.pt
```

Run tests:

```bash
cd backend && python -m pytest -q
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 — it proxies `/api` to the backend on port 8000.

### ML pipeline

See `ml/README.md` for exporting from CVAT, converting to YOLO format,
training, and evaluating.

## Configuration you'll want to revisit

- `ml/configs/damage_classes.yaml` — the 8-class taxonomy (scratch, dent,
  crack, glass_shatter, lamp_broken, tire_damage, bumper_dent, paint_chip)
  and the area-ratio thresholds used to bucket severity into
  minor/moderate/severe. Placeholder thresholds — tune once real detections
  are available.
- `backend/app/data/pricing.json` — repair cost per (damage type,
  severity), currently placeholder numbers. Replace with real workshop
  quotes before this is customer-facing.

See `CONTRIBUTING.md` for the day-to-day workflow.
