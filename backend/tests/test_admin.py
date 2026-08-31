from app.auth import hash_password
from app.models import User, UserRole


def create_admin_directly(db_session, *, email="admin@test.com", phone="09190000001"):
    """Admin accounts can't be created through the public API, so tests create
    one directly via the DB session (mirroring what create_admin.py does)."""
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


def test_admin_role_cannot_self_register(client):
    from .conftest import get_captcha_pair

    captcha_id, code = get_captcha_pair(client)
    r = client.post(
        "/api/auth/register",
        json={
            "full_name": "Hacker",
            "email": "hacker@test.com",
            "phone_number": "09199999999",
            "password": "pass123",
            "role": "admin",
            "captcha_id": captcha_id,
            "captcha_answer": code,
        },
    )
    assert r.status_code == 400
    assert "مدیر گروه" in r.json()["detail"]


def test_admin_can_view_system_stats(client, db_session, professor, approved_project):
    admin = create_admin_directly(db_session)
    headers = login_as(client, admin.email)

    r = client.get("/api/admin/stats", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert body["total_projects"] == 1
    assert body["active_projects"] == 1
    assert body["total_professors"] == 1
    assert body["total_students"] == 1


def test_non_admin_cannot_view_admin_stats(client, professor):
    r = client.get("/api/admin/stats", headers=professor["headers"])
    assert r.status_code == 403


def test_admin_can_list_all_users(client, db_session, professor, student):
    admin = create_admin_directly(db_session)
    headers = login_as(client, admin.email)

    r = client.get("/api/admin/users", headers=headers)
    assert r.status_code == 200
    emails = {u["email"] for u in r.json()}
    assert professor["user"]["email"] in emails
    assert student["user"]["email"] in emails
    assert admin.email in emails


def test_admin_can_filter_users_by_role(client, db_session, professor, student):
    admin = create_admin_directly(db_session)
    headers = login_as(client, admin.email)

    r = client.get("/api/admin/users", params={"role": "student"}, headers=headers)
    assert r.status_code == 200
    assert all(u["role"] == "student" for u in r.json())


def test_non_admin_cannot_list_all_users(client, student):
    r = client.get("/api/admin/users", headers=student["headers"])
    assert r.status_code == 403


def test_admin_sees_every_project_regardless_of_ownership(
    client, db_session, professor, other_student, approved_project
):
    admin = create_admin_directly(db_session)
    headers = login_as(client, admin.email)

    # a second project the admin has no relation to
    client.post(
        "/api/projects", json={"title": "پروژه دوم"}, headers=professor["headers"]
    )

    r = client.get("/api/projects", headers=headers)
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_admin_can_view_any_single_project(
    client, db_session, other_student, approved_project
):
    admin = create_admin_directly(db_session)
    headers = login_as(client, admin.email)

    r = client.get(f"/api/projects/{approved_project['id']}", headers=headers)
    assert r.status_code == 200


def test_admin_can_view_current_invite_code(client, db_session):
    admin = create_admin_directly(db_session)
    headers = login_as(client, admin.email)

    r = client.get("/api/admin/settings", headers=headers)
    assert r.status_code == 200
    assert r.json()["professor_invite_code"]


def test_non_admin_cannot_view_settings(client, professor):
    r = client.get("/api/admin/settings", headers=professor["headers"])
    assert r.status_code == 403


def test_admin_can_change_invite_code(client, db_session):
    admin = create_admin_directly(db_session)
    headers = login_as(client, admin.email)

    r = client.patch(
        "/api/admin/settings",
        json={"professor_invite_code": "new-secret-code"},
        headers=headers,
    )
    assert r.status_code == 200
    assert r.json()["professor_invite_code"] == "new-secret-code"

    r2 = client.get("/api/admin/settings", headers=headers)
    assert r2.json()["professor_invite_code"] == "new-secret-code"


def test_non_admin_cannot_change_invite_code(client, professor):
    r = client.patch(
        "/api/admin/settings",
        json={"professor_invite_code": "hacked-code"},
        headers=professor["headers"],
    )
    assert r.status_code == 403


def test_updated_invite_code_is_enforced_at_registration(client, db_session):
    from .conftest import get_captcha_pair

    admin = create_admin_directly(db_session)
    headers = login_as(client, admin.email)
    client.patch(
        "/api/admin/settings",
        json={"professor_invite_code": "rotated-code"},
        headers=headers,
    )

    # the old default code no longer works
    captcha_id, code = get_captcha_pair(client)
    r = client.post(
        "/api/auth/register",
        json={
            "full_name": "استاد جدید",
            "email": "newprof@test.com",
            "phone_number": "09121230000",
            "password": "password123",
            "role": "professor",
            "captcha_id": captcha_id,
            "captcha_answer": code,
            "invite_code": "dev-professor-code",
        },
    )
    assert r.status_code == 400

    # the new code works
    captcha_id, code = get_captcha_pair(client)
    r2 = client.post(
        "/api/auth/register",
        json={
            "full_name": "استاد جدید",
            "email": "newprof@test.com",
            "phone_number": "09121230000",
            "password": "password123",
            "role": "professor",
            "captcha_id": captcha_id,
            "captcha_answer": code,
            "invite_code": "rotated-code",
        },
    )
    assert r2.status_code == 201
