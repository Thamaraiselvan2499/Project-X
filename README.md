# Project X — Car Damage Annotation & Repair Estimator

A customer-facing flow for estimating car repair costs: log in with a
mobile number and car number, describe the car, point out where it's
damaged on a rotatable 3D model, upload a photo per damaged part, and get
an itemized repair estimate powered by an ML damage detector.

**Team:** Thamaraiselvan (repo owner), Rajana, Ranjini — AI Engineers.

## Status

- ✅ Damage annotation of car images (by damage type) — done in CVAT.
- ✅ CVAT export → YOLO dataset converter, training + evaluation scripts.
- ✅ Backend: detection, severity, quotation, persistence (users/cars/
  reports), all tested. Detector runs in demo/stub mode until real trained
  weights are dropped in (see `ml/README.md`).
- ✅ Frontend: login → car details → 3D damage picker → photo upload →
  itemized report, all wired to the backend.
- ⏳ Not yet done: real OTP/auth (see the caveat in `CONTRIBUTING.md`),
  training on enough real data to generalize, real repair pricing.

## How it works

```
Customer flow (frontend):
  Login (mobile + car number, auto-creates account)
    -> Car details (name/brand/variant/body type)
    -> 3D viewer: rotate a schematic car model, click damaged parts
    -> Upload one photo per selected part
    -> Itemized repair estimate

Per uploaded photo (backend):
  POST /api/reports/{id}/items (part, photo)
    -> backend/app/services/detector.py     (trained model, or stub if none)
    -> backend/app/services/severity.py     (area ratio -> minor/moderate/severe)
    -> backend/app/services/quotation.py    (severity -> cost, from pricing.json)
    -> saved as a DamageItem row, tied to the part and the report

Training pipeline (offline, ml/):
  CVAT export -> ml/scripts/cvat_to_yolo.py -> YOLO dataset
    -> ml/scripts/train.py (YOLOv8) -> weights -> MODEL_WEIGHTS_PATH
```

See `docs/ARCHITECTURE.md` for more detail, including why detection (not
classification) and why area-ratio severity.

## Repo layout

```
backend/    FastAPI service: auth, cars, reports, detection, severity, quotation, DB
ml/         CVAT->YOLO conversion, training, evaluation scripts
frontend/   React (Vite) customer flow: login, car details, 3D viewer, upload, report
docs/       Architecture notes
```

## Quickstart

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

First run creates a local SQLite DB at `backend/app/data/app.db` (gitignored
— every environment has its own). Without trained model weights, damage
detection runs in **stub mode**: fixed placeholder detections, so the
whole pipeline (severity, quotation, persistence, frontend) is testable
before training finishes. Once you have weights (see `ml/README.md`):

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

- `ml/configs/damage_classes.yaml` — the 12-class damage taxonomy and the
  22-label car-part taxonomy (both sourced from the real CVAT project),
  plus the area-ratio thresholds used to bucket severity into
  minor/moderate/severe. Thresholds are calibrated against the one small
  example dataset checked in — recalibrate as more data comes in.
- `backend/app/data/pricing.json` — repair cost per (damage type,
  severity), currently placeholder numbers. Not yet part-aware (a dent on
  a bumper costs the same as a dent on a door) — see `docs/ARCHITECTURE.md`
  for how part selection could feed into pricing next.
- Login has **no OTP / real auth** yet — a mobile number + car number
  that hasn't been seen before is auto-created, no verification. Fine for
  an internal pilot, not for a real launch. See `CONTRIBUTING.md`.

See `CONTRIBUTING.md` for the day-to-day workflow.
