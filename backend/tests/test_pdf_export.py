from app.auth import hash_password
from app.models import User, UserRole


def create_admin_directly(db_session, *, email="pdf-admin@test.com", phone="09190000009"):
    db = db_session()
    try:
        admin = User(
            full_name="مدیر تست",
            email=email,
            phone_number=phone,
            hashed_password=hash_password("password123"),
            role=UserRole.ADMIN,
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        db.expunge(admin)
        return admin
    finally:
        db.close()


def login_as(client, email, password="password123"):
    r = client.post("/api/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_owner_professor_can_export_pdf(client, professor, approved_project):
    r = client.get(
        f"/api/projects/{approved_project['id']}/export-pdf",
        headers=professor["headers"],
    )
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert r.content[:4] == b"%PDF"
    assert len(r.content) > 500


def test_assigned_student_can_export_pdf(client, student, approved_project):
    r = client.get(
        f"/api/projects/{approved_project['id']}/export-pdf",
        headers=student["headers"],
    )
    assert r.status_code == 200
    assert r.content[:4] == b"%PDF"


def test_unrelated_student_cannot_export_pdf_of_assigned_project(
    client, other_student, approved_project
):
    r = client.get(
        f"/api/projects/{approved_project['id']}/export-pdf",
        headers=other_student["headers"],
    )
    assert r.status_code == 403


def test_export_pdf_includes_reports_and_grades(client, professor, student, approved_project):
    r = client.post(
        f"/api/projects/{approved_project['id']}/reports",
        data={"content": "گزارش هفته اول"},
        headers=student["headers"],
    )
    assert r.status_code == 201, r.text

    r = client.post(
        f"/api/projects/{approved_project['id']}/grades",
        json={"stage": "میان‌ترم", "score": 18, "comment": "خوب"},
        headers=professor["headers"],
    )
    assert r.status_code == 201, r.text

    r = client.get(
        f"/api/projects/{approved_project['id']}/export-pdf",
        headers=professor["headers"],
    )
    assert r.status_code == 200
    assert r.content[:4] == b"%PDF"
    assert len(r.content) > 1000


def test_admin_can_export_pdf_of_any_project(client, db_session, approved_project):
    admin = create_admin_directly(db_session)
    headers = login_as(client, admin.email)

    r = client.get(
        f"/api/projects/{approved_project['id']}/export-pdf",
        headers=headers,
    )
    assert r.status_code == 200
    assert r.content[:4] == b"%PDF"
