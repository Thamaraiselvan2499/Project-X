"""Points the app at a throwaway SQLite DB/uploads dir for the whole test
session, set *before* anything imports app.config (pytest loads conftest.py
ahead of collecting test modules), so tests never touch real local data and
start from a clean slate every run."""
import os
import shutil
from pathlib import Path

_TEST_DATA_DIR = Path(__file__).resolve().parent / "_test_data"
shutil.rmtree(_TEST_DATA_DIR, ignore_errors=True)

os.environ["DATABASE_PATH"] = str(_TEST_DATA_DIR / "app.db")
os.environ["UPLOADS_DIR"] = str(_TEST_DATA_DIR / "uploads")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture()
def client():
    # Context-manager form runs FastAPI's lifespan (init_db()) — a bare
    # TestClient(app) doesn't, which would leave tables missing for any
    # test that touches the database.
    with TestClient(app) as c:
        yield c
