# Contributing

Team: Thamaraiselvan, Rajana, Ranjini.

## Suggested split (adjust as needed)

The three main areas are largely independent, so working in parallel
without stepping on each other is straightforward:

- **ML / data pipeline** (`ml/`): pulling CVAT exports in, converting to
  YOLO format, training, tuning severity thresholds.
- **Backend** (`backend/`): API, quotation/pricing logic, integrating
  trained weights, tests.
- **Frontend** (`frontend/`): the login → car details → 3D viewer → upload
  → report flow, the 3D car/hotspot layout (`frontend/src/car3d/`).

Pick whichever matches your focus; the interfaces between them are small
and explicit (`data.yaml` between ML and training, `MODEL_WEIGHTS_PATH`
between ML and backend, `/api/taxonomy` + the reports API contract between
backend and frontend), so a change on one side rarely blocks the others.

## Login has no OTP / real auth yet

`POST /api/auth/login` auto-creates a `User` (keyed on mobile number) and
`Car` (keyed on car number) the first time that pair is seen — there's no
verification that the person logging in actually owns that mobile number.
This is a deliberate scope cut to unblock the rest of the flow (car
details, the 3D viewer, uploads, reports) without waiting on a phone-OTP
integration. **Don't point this at real customer data or deploy it
anywhere public without adding real verification first** (Firebase Phone
Auth is the lowest-setup option — see `docs/ARCHITECTURE.md`).

## Branching

- Branch off the default branch: `git checkout -b <yourname>/<short-description>`
  (e.g. `rajana/train-yolov8-v1`, `ranjini/quotation-ui-polish`).
- Open a PR against the default branch when ready for review.
- Small, focused PRs over one giant one — easier to review with a 3-person team.

## Before opening a PR

- Backend changes: `cd backend && python -m pytest -q`
- Frontend changes: `cd frontend && npm run build` (catches type/import errors)
- ML script changes: run them against the small synthetic/sample case
  described in `ml/README.md`, or a small slice of real data, before a full
  training run.

## Changing the damage taxonomy

The class list lives in **one place**: `ml/configs/damage_classes.yaml`.
If you add/rename/remove a damage type:

1. Update `ml/configs/damage_classes.yaml`.
2. Update the corresponding CVAT project's label list to match (exact
   names — `cvat_to_yolo.py` normalizes case/spacing but not synonyms).
3. Add a cost entry for the new class in `backend/app/data/pricing.json`
   (minor/moderate/severe) — an unmapped class is flagged `needs_review`
   with cost 0 rather than crashing, but it should still get a real price.
4. Re-run `cvat_to_yolo.py` and retrain.

**Changing `part_labels` specifically** also means updating
`frontend/src/car3d/buildCar.js`'s `HOTSPOT_LAYOUT` — the 3D viewer's
clickable parts are a hardcoded list there, not fetched from
`/api/taxonomy` at render time. Removing or renaming a part in the yaml
without updating `HOTSPOT_LAYOUT` leaves a clickable hotspot in the UI
that the backend will reject with a 400 when the customer tries to upload
a photo for it.

## Updating repair pricing

Edit `backend/app/data/pricing.json` directly — it's plain JSON, no code
change needed. `backend/tests/test_quotation.py` has hardcoded expected
costs, so update those numbers too if you change the placeholder prices
it asserts against.

## Model weights

Trained weights (`*.pt`) are gitignored — they're large and reproducible
from `ml/scripts/train.py`. Share them via whatever the team's model
registry/storage ends up being (not committed to git). Point the backend
at a local copy with `MODEL_WEIGHTS_PATH`.
