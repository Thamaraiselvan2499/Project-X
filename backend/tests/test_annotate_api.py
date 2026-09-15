import io

from fastapi.testclient import TestClient
from PIL import Image

from app.main import app

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


def test_annotate_runs_in_stub_mode_without_trained_weights():
    files = {"file": ("car.jpg", _sample_image_bytes(), "image/jpeg")}
    response = client.post("/api/annotate", files=files)
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
