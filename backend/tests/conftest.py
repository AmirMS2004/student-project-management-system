import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.main import app  # noqa: E402
from app.database import Base, get_db  # noqa: E402
from app.config import PROFESSOR_INVITE_CODE  # noqa: E402
from app import captcha as captcha_module  # noqa: E402
from app import file_storage  # noqa: E402


@pytest.fixture()
def db_session(tmp_path):
    """Give every test its own throwaway SQLite file so tests never touch app.db
    or interfere with each other."""
    db_path = tmp_path / "test.db"
    engine = create_engine(
        f"sqlite:///{db_path}", connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestingSessionLocal
    app.dependency_overrides.clear()
    engine.dispose()


@pytest.fixture()
def upload_dir(tmp_path, monkeypatch):
    """Redirect the shared file_storage module's UPLOAD_DIR to a throwaway
    folder so tests never write into the real backend/uploads/ directory."""
    path = tmp_path / "uploads"
    path.mkdir()
    monkeypatch.setattr(file_storage, "UPLOAD_DIR", path)
    return path


@pytest.fixture()
def client(db_session, upload_dir):
    return TestClient(app)


def get_captcha_pair(client):
    """Fetch a fresh captcha and read its plaintext code straight from the
    in-memory store (the same trick used for manual testing during development)."""
    r = client.get("/api/auth/captcha")
    data = r.json()
    code, _ = captcha_module._store[data["captcha_id"]]
    return data["captcha_id"], code


@pytest.fixture()
def register_user(client):
    def _register(role="student", *, email, phone_number, full_name=None, invite_code=None):
        captcha_id, code = get_captcha_pair(client)
        payload = {
            "full_name": full_name or f"Test {role.title()}",
            "email": email,
            "phone_number": phone_number,
            "password": "password123",
            "role": role,
            "captcha_id": captcha_id,
            "captcha_answer": code,
        }
        if role == "professor":
            payload["invite_code"] = invite_code or PROFESSOR_INVITE_CODE
        r = client.post("/api/auth/register", json=payload)
        assert r.status_code == 201, r.text
        data = r.json()
        return {
            "token": data["access_token"],
            "user": data["user"],
            "headers": {"Authorization": f"Bearer {data['access_token']}"},
        }

    return _register


@pytest.fixture()
def professor(register_user):
    return register_user(
        role="professor", email="professor@test.com", phone_number="09100000001"
    )


@pytest.fixture()
def student(register_user):
    return register_user(
        role="student", email="student@test.com", phone_number="09200000001"
    )


@pytest.fixture()
def other_student(register_user):
    return register_user(
        role="student", email="other-student@test.com", phone_number="09200000002"
    )


@pytest.fixture()
def open_project(client, professor):
    r = client.post(
        "/api/projects",
        json={"title": "پروژه نمونه", "abstract": "چکیده نمونه"},
        headers=professor["headers"],
    )
    assert r.status_code == 201, r.text
    return r.json()


@pytest.fixture()
def approved_project(client, professor, student, open_project):
    r = client.post(
        f"/api/projects/{open_project['id']}/requests",
        json={},
        headers=student["headers"],
    )
    assert r.status_code == 201, r.text
    request_id = r.json()["id"]

    r2 = client.patch(
        f"/api/requests/{request_id}",
        json={"approve": True},
        headers=professor["headers"],
    )
    assert r2.status_code == 200, r2.text

    r3 = client.get(f"/api/projects/{open_project['id']}", headers=professor["headers"])
    return r3.json()
