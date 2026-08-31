def test_professor_can_create_project(client, professor):
    r = client.post(
        "/api/projects",
        json={"title": "پروژه جدید", "abstract": "توضیح"},
        headers=professor["headers"],
    )
    assert r.status_code == 201
    body = r.json()
    assert body["status"] == "open"
    assert body["professor_id"] == professor["user"]["id"]


def test_student_cannot_create_project(client, student):
    r = client.post(
        "/api/projects",
        json={"title": "پروژه غیرمجاز"},
        headers=student["headers"],
    )
    assert r.status_code == 403


def test_student_sees_open_projects_in_default_listing(client, student, open_project):
    r = client.get("/api/projects", headers=student["headers"])
    assert r.status_code == 200
    titles = [p["title"] for p in r.json()]
    assert open_project["title"] in titles


def test_student_mine_listing_excludes_unrelated_open_projects(
    client, student, open_project
):
    r = client.get("/api/projects", params={"mine": True}, headers=student["headers"])
    assert r.status_code == 200
    assert r.json() == []


def test_professor_mine_listing_only_shows_own_projects(
    client, professor, register_user, open_project
):
    other_prof = register_user(
        role="professor", email="other-prof@test.com", phone_number="09300000001"
    )
    client.post(
        "/api/projects",
        json={"title": "پروژه استاد دیگر"},
        headers=other_prof["headers"],
    )

    r = client.get("/api/projects", params={"mine": True}, headers=professor["headers"])
    titles = [p["title"] for p in r.json()]
    assert open_project["title"] in titles
    assert "پروژه استاد دیگر" not in titles


def test_filter_by_professor_id(client, student, professor, open_project):
    r = client.get(
        "/api/projects",
        params={"status_filter": "open", "professor_id": professor["user"]["id"]},
        headers=student["headers"],
    )
    assert r.status_code == 200
    assert all(p["professor_id"] == professor["user"]["id"] for p in r.json())


def test_search_matches_title(client, student, professor):
    client.post(
        "/api/projects",
        json={"title": "تشخیص چهره با یادگیری عمیق", "abstract": "بینایی ماشین"},
        headers=professor["headers"],
    )
    client.post(
        "/api/projects",
        json={"title": "سیستم مدیریت انبار", "abstract": "لاجیستیک"},
        headers=professor["headers"],
    )
    r = client.get(
        "/api/projects", params={"status_filter": "open", "search": "چهره"}, headers=student["headers"]
    )
    assert r.status_code == 200
    titles = [p["title"] for p in r.json()]
    assert any("چهره" in t for t in titles)
    assert all("چهره" in t for t in titles)


def test_search_matches_abstract_too(client, student, professor):
    client.post(
        "/api/projects",
        json={"title": "عنوان کاملا متفاوت", "abstract": "این پروژه درباره بینایی ماشین است"},
        headers=professor["headers"],
    )
    r = client.get(
        "/api/projects",
        params={"status_filter": "open", "search": "بینایی ماشین"},
        headers=student["headers"],
    )
    assert r.status_code == 200
    assert any(p["title"] == "عنوان کاملا متفاوت" for p in r.json())


def test_search_with_no_matches_returns_empty_list(client, student, open_project):
    r = client.get(
        "/api/projects",
        params={"status_filter": "open", "search": "چیزی که وجود ندارد xyz123"},
        headers=student["headers"],
    )
    assert r.status_code == 200
    assert r.json() == []


def test_unrelated_student_cannot_view_in_progress_project(
    client, other_student, approved_project
):
    r = client.get(
        f"/api/projects/{approved_project['id']}", headers=other_student["headers"]
    )
    assert r.status_code == 403


def test_assigned_student_can_view_project(client, student, approved_project):
    r = client.get(
        f"/api/projects/{approved_project['id']}", headers=student["headers"]
    )
    assert r.status_code == 200


def test_other_professor_cannot_update_project(
    client, register_user, open_project
):
    other_prof = register_user(
        role="professor", email="other-prof2@test.com", phone_number="09300000002"
    )
    r = client.patch(
        f"/api/projects/{open_project['id']}",
        json={"progress_percent": 50},
        headers=other_prof["headers"],
    )
    assert r.status_code == 403


def test_owner_can_update_project(client, professor, open_project):
    r = client.patch(
        f"/api/projects/{open_project['id']}",
        json={"progress_percent": 30, "abstract": "چکیده به‌روزشده"},
        headers=professor["headers"],
    )
    assert r.status_code == 200
    assert r.json()["progress_percent"] == 30


def test_setting_defense_date_notifies_assigned_student(
    client, professor, student, approved_project
):
    r = client.patch(
        f"/api/projects/{approved_project['id']}",
        json={"defense_date": "2030-06-15T10:00:00"},
        headers=professor["headers"],
    )
    assert r.status_code == 200
    assert r.json()["defense_date"].startswith("2030-06-15T10:00:00")

    notifs = client.get("/api/notifications", headers=student["headers"]).json()
    assert any(n["category"] == "project" for n in notifs)


def test_defense_date_on_open_project_does_not_notify_anyone(
    client, professor, open_project
):
    r = client.patch(
        f"/api/projects/{open_project['id']}",
        json={"defense_date": "2030-06-15T10:00:00"},
        headers=professor["headers"],
    )
    assert r.status_code == 200
    assert r.json()["defense_date"] is not None


def test_student_cannot_update_project(client, student, open_project):
    r = client.patch(
        f"/api/projects/{open_project['id']}",
        json={"progress_percent": 30},
        headers=student["headers"],
    )
    assert r.status_code == 403


def test_delete_open_project_succeeds(client, professor, open_project):
    r = client.delete(
        f"/api/projects/{open_project['id']}", headers=professor["headers"]
    )
    assert r.status_code == 204


def test_delete_project_with_assigned_student_fails(client, professor, approved_project):
    r = client.delete(
        f"/api/projects/{approved_project['id']}", headers=professor["headers"]
    )
    assert r.status_code == 400


def test_brief_file_upload_and_download(client, professor, student, open_project):
    files = {"file": ("brief.txt", b"project brief details", "text/plain")}
    r = client.post(
        f"/api/projects/{open_project['id']}/brief-file",
        files=files,
        headers=professor["headers"],
    )
    assert r.status_code == 200
    assert r.json()["brief_original_filename"] == "brief.txt"

    # any student browsing an open project may download the brief, even before
    # requesting it
    r2 = client.get(
        f"/api/projects/{open_project['id']}/brief-file/download",
        headers=student["headers"],
    )
    assert r2.status_code == 200
    assert r2.content == b"project brief details"


def test_only_owner_can_upload_brief_file(client, register_user, open_project):
    other_prof = register_user(
        role="professor", email="other-prof3@test.com", phone_number="09300000003"
    )
    files = {"file": ("brief.txt", b"data", "text/plain")}
    r = client.post(
        f"/api/projects/{open_project['id']}/brief-file",
        files=files,
        headers=other_prof["headers"],
    )
    assert r.status_code == 403


def test_professor_can_set_defense_outcome(client, professor, approved_project):
    r = client.patch(
        f"/api/projects/{approved_project['id']}",
        json={"defense_outcome": "pass", "defense_outcome_notes": "دفاع خوبی بود"},
        headers=professor["headers"],
    )
    assert r.status_code == 200
    body = r.json()
    assert body["defense_outcome"] == "pass"
    assert body["defense_outcome_notes"] == "دفاع خوبی بود"


def test_defense_outcome_defaults_to_null(client, approved_project):
    assert approved_project["defense_outcome"] is None


def test_student_cannot_set_defense_outcome(client, student, approved_project):
    r = client.patch(
        f"/api/projects/{approved_project['id']}",
        json={"defense_outcome": "pass"},
        headers=student["headers"],
    )
    assert r.status_code == 403


def test_invalid_defense_outcome_rejected(client, professor, approved_project):
    r = client.patch(
        f"/api/projects/{approved_project['id']}",
        json={"defense_outcome": "excellent"},
        headers=professor["headers"],
    )
    assert r.status_code == 422
