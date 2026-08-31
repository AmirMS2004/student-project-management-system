def test_professor_upload_is_categorized_as_required(client, professor, approved_project):
    files = {"file": ("syllabus.pdf", b"syllabus content", "application/pdf")}
    r = client.post(
        f"/api/projects/{approved_project['id']}/files",
        files=files,
        data={"description": "سرفصل درس"},
        headers=professor["headers"],
    )
    assert r.status_code == 201
    assert r.json()["category"] == "required"


def test_student_upload_is_categorized_as_submission(client, student, approved_project):
    files = {"file": ("code.zip", b"zip content", "application/zip")}
    r = client.post(
        f"/api/projects/{approved_project['id']}/files",
        files=files,
        headers=student["headers"],
    )
    assert r.status_code == 201
    assert r.json()["category"] == "submission"


def test_outsider_cannot_upload_file(client, other_student, approved_project):
    files = {"file": ("hack.txt", b"data", "text/plain")}
    r = client.post(
        f"/api/projects/{approved_project['id']}/files",
        files=files,
        headers=other_student["headers"],
    )
    assert r.status_code == 403


def test_file_list_and_download_roundtrip(client, professor, student, approved_project):
    files = {"file": ("notes.txt", b"important notes", "text/plain")}
    r = client.post(
        f"/api/projects/{approved_project['id']}/files",
        files=files,
        headers=professor["headers"],
    )
    file_id = r.json()["id"]

    r2 = client.get(
        f"/api/projects/{approved_project['id']}/files", headers=student["headers"]
    )
    assert r2.status_code == 200
    assert len(r2.json()) == 1

    r3 = client.get(f"/api/files/{file_id}/download", headers=student["headers"])
    assert r3.status_code == 200
    assert r3.content == b"important notes"


def test_outsider_cannot_download_file(client, professor, other_student, approved_project):
    files = {"file": ("secret.txt", b"secret", "text/plain")}
    r = client.post(
        f"/api/projects/{approved_project['id']}/files",
        files=files,
        headers=professor["headers"],
    )
    file_id = r.json()["id"]

    r2 = client.get(f"/api/files/{file_id}/download", headers=other_student["headers"])
    assert r2.status_code == 403
