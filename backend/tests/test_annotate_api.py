import io

from fastapi.testclient import TestClient
from PIL import Image

from app.main import app
from app.services import detector

client = TestClient(app)


def _sample_image_bytes(width: int = 200, height: int = 150) -> bytes:
    image = Image.new("RGB", (width, height), color=(120, 120, 120))
    buf = io.BytesIO()
    image.save(buf, format="JPEG")
    return buf.getvalue()


def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_annotate_runs_in_stub_mode_without_trained_weights(monkeypatch, tmp_path):
    # detector._load_model() is memoized process-wide and reads its own
    # module-level MODEL_WEIGHTS_PATH, so this can't just rely on there
    # being no file at the default path — a dev machine that's actually
    # trained a model (as this repo's ml/README.md walks through) would
    # make that assumption false and this test flaky. Force stub mode
    # explicitly instead.
    monkeypatch.setattr(detector, "MODEL_WEIGHTS_PATH", tmp_path / "does_not_exist.pt")
    detector._load_model.cache_clear()

    files = {"file": ("car.jpg", _sample_image_bytes(), "image/jpeg")}
    response = client.post("/api/annotate", files=files)
    detector._load_model.cache_clear()  # don't leak the stubbed path into other tests

    assert response.status_code == 200

    body = response.json()
    assert body["model_mode"] == "stub"
    assert body["image_width"] == 200
    assert body["image_height"] == 150
    assert len(body["detections"]) > 0
    assert body["quotation"]["total"] > 0


def test_annotate_rejects_non_image_upload():
    files = {"file": ("notes.txt", b"hello world", "text/plain")}
    response = client.post("/api/annotate", files=files)
    assert response.status_code == 400
