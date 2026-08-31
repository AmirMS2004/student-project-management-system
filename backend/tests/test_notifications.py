def test_new_request_creates_a_notification_for_the_professor(
    client, professor, student, open_project
):
    client.post(
        f"/api/projects/{open_project['id']}/requests", json={}, headers=student["headers"]
    )
    r = client.get("/api/notifications", headers=professor["headers"])
    assert r.status_code == 200
    notifs = r.json()
    assert len(notifs) == 1
    assert notifs[0]["category"] == "request"
    assert notifs[0]["project_id"] == open_project["id"]
    assert notifs[0]["is_read"] is False


def test_unread_only_filter(client, professor, student, open_project):
    client.post(
        f"/api/projects/{open_project['id']}/requests", json={}, headers=student["headers"]
    )
    notif_id = client.get("/api/notifications", headers=professor["headers"]).json()[0]["id"]
    client.post(f"/api/notifications/{notif_id}/read", headers=professor["headers"])

    r = client.get(
        "/api/notifications", params={"unread_only": True}, headers=professor["headers"]
    )
    assert r.json() == []


def test_project_id_filter(client, professor, student, open_project, register_user):
    other_prof = register_user(
        role="professor", email="other-prof5@test.com", phone_number="09300000005"
    )
    other_project = client.post(
        "/api/projects", json={"title": "پروژه دیگر"}, headers=other_prof["headers"]
    ).json()

    client.post(
        f"/api/projects/{open_project['id']}/requests", json={}, headers=student["headers"]
    )

    r = client.get(
        "/api/notifications",
        params={"project_id": other_project["id"]},
        headers=other_prof["headers"],
    )
    assert r.json() == []


def test_mark_read_by_category_only_affects_that_category(
    client, professor, student, approved_project
):
    client.post(
        f"/api/projects/{approved_project['id']}/reports",
        data={"content": "گزارش هفتگی"},
        headers=student["headers"],
    )
    client.post(
        f"/api/projects/{approved_project['id']}/messages",
        data={"recipient_id": professor["user"]["id"], "content": "سلام"},
        headers=student["headers"],
    )

    r = client.post(
        "/api/notifications/read-by-category",
        params={"project_id": approved_project["id"], "category": "report"},
        headers=professor["headers"],
    )
    assert r.status_code == 200

    remaining = client.get(
        "/api/notifications", params={"unread_only": True}, headers=professor["headers"]
    ).json()
    categories = {n["category"] for n in remaining}
    assert "report" not in categories
    assert "message" in categories


def test_mark_all_read(client, professor, student, open_project):
    client.post(
        f"/api/projects/{open_project['id']}/requests", json={}, headers=student["headers"]
    )
    client.post("/api/notifications/read-all", headers=professor["headers"])

    r = client.get(
        "/api/notifications", params={"unread_only": True}, headers=professor["headers"]
    )
    assert r.json() == []


def test_cannot_mark_someone_elses_notification_as_read(
    client, professor, student, open_project
):
    client.post(
        f"/api/projects/{open_project['id']}/requests", json={}, headers=student["headers"]
    )
    notif_id = client.get("/api/notifications", headers=professor["headers"]).json()[0]["id"]

    r = client.post(f"/api/notifications/{notif_id}/read", headers=student["headers"])
    assert r.status_code == 404
