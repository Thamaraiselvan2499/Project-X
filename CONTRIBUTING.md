# Contributing

Team: Thamaraiselvan, Rajana, Ranjini.

## Suggested split (adjust as needed)

The three main areas are largely independent, so working in parallel
without stepping on each other is straightforward:

- **ML / data pipeline** (`ml/`): pulling CVAT exports in, converting to
  YOLO format, training, tuning severity thresholds.
- **Backend** (`backend/`): API, quotation/pricing logic, integrating
  trained weights, tests.
- **Frontend** (`frontend/`): upload UI, annotated-image rendering,
  quotation display, eventually auth/history if needed.

Pick whichever matches your focus; the interfaces between them are small
and explicit (`data.yaml` between ML and training, `MODEL_WEIGHTS_PATH`
between ML and backend, the `/api/annotate` JSON contract between backend
and frontend), so a change on one side rarely blocks the others.

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
