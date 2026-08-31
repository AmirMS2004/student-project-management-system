def test_student_can_submit_report_without_file(client, student, approved_project):
    r = client.post(
        f"/api/projects/{approved_project['id']}/reports",
        data={"content": "پیشرفت این هفته"},
        headers=student["headers"],
    )
    assert r.status_code == 201
    assert r.json()["attachment_original_filename"] is None


def test_student_can_submit_report_with_file(client, student, approved_project):
    files = {"file": ("weekly.txt", b"weekly progress", "text/plain")}
    r = client.post(
        f"/api/projects/{approved_project['id']}/reports",
        data={"content": "پیشرفت این هفته"},
        files=files,
        headers=student["headers"],
    )
    assert r.status_code == 201
    assert r.json()["attachment_original_filename"] == "weekly.txt"


def test_professor_cannot_submit_report(client, professor, approved_project):
    r = client.post(
        f"/api/projects/{approved_project['id']}/reports",
        data={"content": "not allowed"},
        headers=professor["headers"],
    )
    assert r.status_code == 403


def test_unassigned_student_cannot_submit_report(client, other_student, approved_project):
    r = client.post(
        f"/api/projects/{approved_project['id']}/reports",
        data={"content": "not mine"},
        headers=other_student["headers"],
    )
    assert r.status_code == 403


def test_professor_can_comment_on_report(client, professor, student, approved_project):
    r = client.post(
        f"/api/projects/{approved_project['id']}/reports",
        data={"content": "پیشرفت این هفته"},
        headers=student["headers"],
    )
    report_id = r.json()["id"]

    r2 = client.patch(
        f"/api/reports/{report_id}",
        json={"professor_comment": "عالی بود"},
        headers=professor["headers"],
    )
    assert r2.status_code == 200
    assert r2.json()["professor_comment"] == "عالی بود"


def test_download_report_attachment(client, student, professor, approved_project):
    files = {"file": ("weekly.txt", b"weekly progress content", "text/plain")}
    r = client.post(
        f"/api/projects/{approved_project['id']}/reports",
        data={"content": "گزارش"},
        files=files,
        headers=student["headers"],
    )
    report_id = r.json()["id"]

    r2 = client.get(f"/api/reports/{report_id}/download", headers=professor["headers"])
    assert r2.status_code == 200
    assert r2.content == b"weekly progress content"


def test_outsider_cannot_download_report_attachment(
    client, student, other_student, approved_project
):
    files = {"file": ("weekly.txt", b"secret content", "text/plain")}
    r = client.post(
        f"/api/projects/{approved_project['id']}/reports",
        data={"content": "گزارش"},
        files=files,
        headers=student["headers"],
    )
    report_id = r.json()["id"]

    r2 = client.get(
        f"/api/reports/{report_id}/download", headers=other_student["headers"]
    )
    assert r2.status_code == 403
