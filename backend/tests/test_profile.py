def test_user_can_update_own_full_name(client, student):
    r = client.patch(
        "/api/auth/me", json={"full_name": "نام جدید"}, headers=student["headers"]
    )
    assert r.status_code == 200
    assert r.json()["full_name"] == "نام جدید"


def test_user_can_update_email(client, student):
    r = client.patch(
        "/api/auth/me", json={"email": "new-email@test.com"}, headers=student["headers"]
    )
    assert r.status_code == 200
    assert r.json()["email"] == "new-email@test.com"

    # login works with the new email afterwards
    r2 = client.post(
        "/api/auth/login",
        json={"email": "new-email@test.com", "password": "password123"},
    )
    assert r2.status_code == 200


def test_updating_email_to_an_existing_one_is_rejected(client, student, professor):
    r = client.patch(
        "/api/auth/me",
        json={"email": professor["user"]["email"]},
        headers=student["headers"],
    )
    assert r.status_code == 400
    assert "ایمیل" in r.json()["detail"]


def test_updating_phone_to_an_existing_one_is_rejected(client, student, professor):
    r = client.patch(
        "/api/auth/me",
        json={"phone_number": professor["user"]["phone_number"]},
        headers=student["headers"],
    )
    assert r.status_code == 400
    assert "موبایل" in r.json()["detail"]


def test_updating_to_own_current_email_is_a_no_op(client, student):
    r = client.patch(
        "/api/auth/me",
        json={"email": student["user"]["email"]},
        headers=student["headers"],
    )
    assert r.status_code == 200


def test_invalid_phone_format_is_rejected(client, student):
    r = client.patch(
        "/api/auth/me", json={"phone_number": "12345"}, headers=student["headers"]
    )
    assert r.status_code == 422


def test_profile_update_requires_authentication(client):
    r = client.patch("/api/auth/me", json={"full_name": "کسی"})
    assert r.status_code == 401


def test_user_can_change_password(client, student):
    r = client.post(
        "/api/auth/me/password",
        json={"current_password": "password123", "new_password": "newpassword456"},
        headers=student["headers"],
    )
    assert r.status_code == 200

    r2 = client.post(
        "/api/auth/login",
        json={"email": student["user"]["email"], "password": "newpassword456"},
    )
    assert r2.status_code == 200

    r3 = client.post(
        "/api/auth/login",
        json={"email": student["user"]["email"], "password": "password123"},
    )
    assert r3.status_code == 401


def test_change_password_rejects_wrong_current_password(client, student):
    r = client.post(
        "/api/auth/me/password",
        json={"current_password": "wrong-password", "new_password": "newpassword456"},
        headers=student["headers"],
    )
    assert r.status_code == 400


def test_change_password_requires_authentication(client):
    r = client.post(
        "/api/auth/me/password",
        json={"current_password": "x", "new_password": "newpassword456"},
    )
    assert r.status_code == 401
