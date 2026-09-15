import io

import pytest
from PIL import Image

from app.services import detector


def _sample_image_bytes(width: int = 200, height: int = 150) -> bytes:
    image = Image.new("RGB", (width, height), color=(120, 120, 120))
    buf = io.BytesIO()
    image.save(buf, format="JPEG")
    return buf.getvalue()


@pytest.fixture(autouse=True)
def force_stub_detector(monkeypatch, tmp_path):
    # These tests assert on specific stub detections/costs — force stub
    # mode regardless of whether this machine happens to have trained
    # weights sitting at the default MODEL_WEIGHTS_PATH (see the same
    # pattern in test_annotate_api.py).
    monkeypatch.setattr(detector, "MODEL_WEIGHTS_PATH", tmp_path / "does_not_exist.pt")
    detector._load_model.cache_clear()
    yield
    detector._load_model.cache_clear()


def test_login_creates_user_and_car_on_first_use(client):
    response = client.post("/api/auth/login", json={"mobile_number": "9000000001", "car_number": "TN01AA0001"})
    assert response.status_code == 200

    body = response.json()
    assert body["mobile_number"] == "9000000001"
    assert body["car"]["car_number"] == "TN01AA0001"
    assert body["car"]["is_new"] is True
    assert body["car"]["car_name"] is None


def test_login_is_idempotent_and_reflects_saved_car_details(client):
    mobile, car_number = "9000000002", "TN01AA0002"
    client.post("/api/auth/login", json={"mobile_number": mobile, "car_number": car_number})

    update = client.put(
        f"/api/cars/{car_number}",
        json={"car_name": "Swift", "brand": "Maruti Suzuki", "variant": "VXI", "body_type": "hatchback"},
    )
    assert update.status_code == 200
    assert update.json()["is_new"] is False

    second_login = client.post("/api/auth/login", json={"mobile_number": mobile, "car_number": car_number})
    car = second_login.json()["car"]
    assert car["is_new"] is False
    assert car["car_name"] == "Swift"
    assert car["body_type"] == "hatchback"


def test_car_update_requires_login_first(client):
    response = client.put(
        "/api/cars/DOES-NOT-EXIST",
        json={"car_name": "X", "brand": "Y", "variant": "Z", "body_type": "sedan"},
    )
    assert response.status_code == 404


def test_taxonomy_lists_classes_and_parts(client):
    response = client.get("/api/taxonomy")
    assert response.status_code == 200
    body = response.json()
    assert "dent" in body["damage_classes"]
    assert "front_bumper" in body["part_labels"]
    assert "hatchback" in body["body_types"]


def test_create_report_requires_existing_car(client):
    response = client.post("/api/reports", json={"car_number": "DOES-NOT-EXIST"})
    assert response.status_code == 404


def test_add_item_rejects_unknown_part(client):
    mobile, car_number = "9000000003", "TN01AA0003"
    client.post("/api/auth/login", json={"mobile_number": mobile, "car_number": car_number})
    report_id = client.post("/api/reports", json={"car_number": car_number}).json()["report_id"]

    files = {"file": ("car.jpg", _sample_image_bytes(), "image/jpeg")}
    response = client.post(f"/api/reports/{report_id}/items", data={"part": "not_a_real_part"}, files=files)
    assert response.status_code == 400


def test_add_item_to_missing_report_404(client):
    files = {"file": ("car.jpg", _sample_image_bytes(), "image/jpeg")}
    response = client.post("/api/reports/999999/items", data={"part": "front_bumper"}, files=files)
    assert response.status_code == 404


def test_full_report_flow_aggregates_multiple_parts(client):
    mobile, car_number = "9000000004", "TN01AA0004"
    client.post("/api/auth/login", json={"mobile_number": mobile, "car_number": car_number})
    client.put(
        f"/api/cars/{car_number}",
        json={"car_name": "Brezza", "brand": "Maruti Suzuki", "variant": "ZXI", "body_type": "suv"},
    )
    report_id = client.post("/api/reports", json={"car_number": car_number}).json()["report_id"]

    files = {"file": ("car.jpg", _sample_image_bytes(), "image/jpeg")}
    first = client.post(f"/api/reports/{report_id}/items", data={"part": "front_bumper"}, files=files)
    assert first.status_code == 200
    first_body = first.json()
    # Stub detector always returns its two placeholder detections.
    assert len(first_body["added_items"]) == 2
    assert all(item["part"] == "front_bumper" for item in first_body["added_items"])

    files2 = {"file": ("car2.jpg", _sample_image_bytes(), "image/jpeg")}
    second = client.post(f"/api/reports/{report_id}/items", data={"part": "left_front_door"}, files=files2)
    assert second.status_code == 200

    report = client.get(f"/api/reports/{report_id}")
    assert report.status_code == 200
    report_body = report.json()

    assert len(report_body["items"]) == 4  # 2 from the first upload + 2 from the second
    assert report_body["subtotal"] == sum(item["cost"] for item in report_body["items"])
    assert report_body["total"] == report_body["subtotal"] + report_body["service_fee"]
    parts_seen = {item["part"] for item in report_body["items"]}
    assert parts_seen == {"front_bumper", "left_front_door"}


def test_photo_with_no_detections_still_recorded(client, monkeypatch):
    from app.routers import reports as reports_module
    from app.services.analysis import ImageAnalysis

    # reports.py imports analyze_image_bytes by name, so it must be
    # patched where it's looked up (reports_module), not on the
    # app.services.analysis module itself.
    monkeypatch.setattr(
        reports_module,
        "analyze_image_bytes",
        lambda raw_bytes: ImageAnalysis(width=10, height=10, detections=[], model_mode="stub"),
    )

    mobile, car_number = "9000000005", "TN01AA0005"
    client.post("/api/auth/login", json={"mobile_number": mobile, "car_number": car_number})
    report_id = client.post("/api/reports", json={"car_number": car_number}).json()["report_id"]

    files = {"file": ("car.jpg", _sample_image_bytes(), "image/jpeg")}
    response = client.post(f"/api/reports/{report_id}/items", data={"part": "bonnet"}, files=files)
    assert response.status_code == 200
    body = response.json()
    assert len(body["added_items"]) == 1
    assert body["added_items"][0]["damage_type"] is None
    assert body["added_items"][0]["cost"] == 0.0
    # Service fee still applies — an inspection happened even though no
    # damage was found on this part (matches build_quotation's existing
    # "fee applies whenever there's at least one line item" behavior).
    assert body["report"]["subtotal"] == 0.0
    assert body["report"]["total"] == body["report"]["service_fee"]
