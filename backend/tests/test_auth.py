from app.config import PROFESSOR_INVITE_CODE

from .conftest import get_captcha_pair


def test_student_registration_succeeds(client):
    captcha_id, code = get_captcha_pair(client)
    r = client.post(
        "/api/auth/register",
        json={
            "full_name": "دانشجوی تستی",
            "email": "newstudent@test.com",
            "phone_number": "09210000001",
            "password": "password123",
            "role": "student",
            "captcha_id": captcha_id,
            "captcha_answer": code,
        },
    )
    assert r.status_code == 201
    body = r.json()
    assert body["user"]["role"] == "student"
    assert "access_token" in body


def test_registration_fails_with_wrong_captcha(client):
    captcha_id, _ = get_captcha_pair(client)
    r = client.post(
        "/api/auth/register",
        json={
            "full_name": "کاربر تستی",
            "email": "badcaptcha@test.com",
            "phone_number": "09210000002",
            "password": "password123",
            "role": "student",
            "captcha_id": captcha_id,
            "captcha_answer": "WRONG",
        },
    )
    assert r.status_code == 400


def test_captcha_is_single_use(client):
    captcha_id, code = get_captcha_pair(client)
    payload = {
        "full_name": "کاربر اول",
        "email": "first@test.com",
        "phone_number": "09210000003",
        "password": "password123",
        "role": "student",
        "captcha_id": captcha_id,
        "captcha_answer": code,
    }
    r1 = client.post("/api/auth/register", json=payload)
    assert r1.status_code == 201

    r2 = client.post(
        "/api/auth/register",
        json={**payload, "email": "second@test.com", "phone_number": "09210000004"},
    )
    assert r2.status_code == 400


def test_professor_registration_requires_invite_code(client):
    captcha_id, code = get_captcha_pair(client)
    r = client.post(
        "/api/auth/register",
        json={
            "full_name": "استاد تقلبی",
            "email": "fakeprof@test.com",
            "phone_number": "09210000005",
            "password": "password123",
            "role": "professor",
            "captcha_id": captcha_id,
            "captcha_answer": code,
        },
    )
    assert r.status_code == 400
    assert "دعوت" in r.json()["detail"]


def test_professor_registration_rejects_wrong_invite_code(client):
    captcha_id, code = get_captcha_pair(client)
    r = client.post(
        "/api/auth/register",
        json={
            "full_name": "استاد تقلبی",
            "email": "fakeprof2@test.com",
            "phone_number": "09210000006",
            "password": "password123",
            "role": "professor",
            "captcha_id": captcha_id,
            "captcha_answer": code,
            "invite_code": "wrong-code",
        },
    )
    assert r.status_code == 400


def test_professor_registration_succeeds_with_correct_invite_code(client):
    captcha_id, code = get_captcha_pair(client)
    r = client.post(
        "/api/auth/register",
        json={
            "full_name": "استاد واقعی",
            "email": "realprof@test.com",
            "phone_number": "09210000007",
            "password": "password123",
            "role": "professor",
            "captcha_id": captcha_id,
            "captcha_answer": code,
            "invite_code": PROFESSOR_INVITE_CODE,
        },
    )
    assert r.status_code == 201
    assert r.json()["user"]["role"] == "professor"


def test_duplicate_email_is_rejected(client, student):
    captcha_id, code = get_captcha_pair(client)
    r = client.post(
        "/api/auth/register",
        json={
            "full_name": "دانشجو دوم",
            "email": student["user"]["email"],
            "phone_number": "09210000008",
            "password": "password123",
            "role": "student",
            "captcha_id": captcha_id,
            "captcha_answer": code,
        },
    )
    assert r.status_code == 400
    assert "ایمیل" in r.json()["detail"]


def test_duplicate_phone_number_is_rejected(client, student):
    captcha_id, code = get_captcha_pair(client)
    r = client.post(
        "/api/auth/register",
        json={
            "full_name": "دانشجو دوم",
            "email": "different-email@test.com",
            "phone_number": student["user"]["phone_number"],
            "password": "password123",
            "role": "student",
            "captcha_id": captcha_id,
            "captcha_answer": code,
        },
    )
    assert r.status_code == 400
    assert "موبایل" in r.json()["detail"]


def test_invalid_phone_number_format_is_rejected(client):
    captcha_id, code = get_captcha_pair(client)
    r = client.post(
        "/api/auth/register",
        json={
            "full_name": "کاربر تستی",
            "email": "badphone@test.com",
            "phone_number": "12345",
            "password": "password123",
            "role": "student",
            "captcha_id": captcha_id,
            "captcha_answer": code,
        },
    )
    assert r.status_code == 422


def test_login_succeeds_with_correct_password(client, student):
    r = client.post(
        "/api/auth/login",
        json={"email": student["user"]["email"], "password": "password123"},
    )
    assert r.status_code == 200
    assert "access_token" in r.json()


def test_login_fails_with_wrong_password(client, student):
    r = client.post(
        "/api/auth/login",
        json={"email": student["user"]["email"], "password": "wrong-password"},
    )
    assert r.status_code == 401


def test_me_requires_authentication(client):
    r = client.get("/api/auth/me")
    assert r.status_code == 401


def test_me_returns_current_user(client, student):
    r = client.get("/api/auth/me", headers=student["headers"])
    assert r.status_code == 200
    assert r.json()["email"] == student["user"]["email"]
