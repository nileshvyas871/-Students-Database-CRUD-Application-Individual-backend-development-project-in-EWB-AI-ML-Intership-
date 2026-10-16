import os
import tempfile
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Use a separate test database so tests never alter a user's demo database.
TEST_DB = Path(tempfile.gettempdir()) / "ewb_students_test.sqlite3"
if TEST_DB.exists():
    TEST_DB.unlink()
os.environ["STUDENT_DB_PATH"] = str(TEST_DB)
os.environ["SEED_DEMO_DATA"] = "false"

from fastapi.testclient import TestClient
from app.main import app, init_db

init_db()
client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_student_crud():
    payload = {
        "student_code": "TEST-001",
        "name": "Test Student",
        "date_of_birth": "2005-04-15",
        "email": "test.student@example.com",
        "phone": "+91 90000 00000",
        "course": "AI & Machine Learning",
        "address": "Jaipur",
        "enrollment_date": "2026-10-01",
        "status": "Active",
    }
    created = client.post("/students", json=payload)
    assert created.status_code == 201, created.text
    student_id = created.json()["id"]

    assert client.get(f"/students/{student_id}").status_code == 200
    assert client.get("/students?search=Test").json()["total"] == 1

    updated = client.patch(f"/students/{student_id}", json={"status": "Completed"})
    assert updated.status_code == 200
    assert updated.json()["status"] == "Completed"

    deleted = client.delete(f"/students/{student_id}")
    assert deleted.status_code == 204
    assert client.get(f"/students/{student_id}").status_code == 404


def test_duplicate_email_is_rejected():
    payload = {
        "name": "First Person",
        "date_of_birth": "2004-01-01",
        "email": "same@example.com",
        "enrollment_date": "2026-10-01",
    }
    assert client.post("/students", json=payload).status_code == 201
    second = {**payload, "name": "Second Person"}
    assert client.post("/students", json=second).status_code == 409
