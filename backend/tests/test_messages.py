def test_send_text_only_message(client, professor, student, approved_project):
    r = client.post(
        f"/api/projects/{approved_project['id']}/messages",
        data={"recipient_id": student["user"]["id"], "content": "سلام"},
        headers=professor["headers"],
    )
    assert r.status_code == 201
    assert r.json()["content"] == "سلام"
    assert r.json()["attachment_original_filename"] is None


def test_send_message_with_file_and_no_text(client, student, professor, approved_project):
    files = {"file": ("note.txt", b"file contents", "text/plain")}
    r = client.post(
        f"/api/projects/{approved_project['id']}/messages",
        data={"recipient_id": professor["user"]["id"]},
        files=files,
        headers=student["headers"],
    )
    assert r.status_code == 201
    assert r.json()["content"] is None
    assert r.json()["attachment_original_filename"] == "note.txt"


def test_message_requires_content_or_file(client, professor, student, approved_project):
    r = client.post(
        f"/api/projects/{approved_project['id']}/messages",
        data={"recipient_id": student["user"]["id"]},
        headers=professor["headers"],
    )
    assert r.status_code == 400


def test_cannot_send_message_to_self(client, professor, student, approved_project):
    r = client.post(
        f"/api/projects/{approved_project['id']}/messages",
        data={"recipient_id": professor["user"]["id"], "content": "سلام"},
        headers=professor["headers"],
    )
    assert r.status_code == 400


def test_cannot_send_message_to_unrelated_user(
    client, professor, other_student, approved_project
):
    r = client.post(
        f"/api/projects/{approved_project['id']}/messages",
        data={"recipient_id": other_student["user"]["id"], "content": "سلام"},
        headers=professor["headers"],
    )
    assert r.status_code == 400


def test_outsider_cannot_send_message(client, other_student, professor, approved_project):
    r = client.post(
        f"/api/projects/{approved_project['id']}/messages",
        data={"recipient_id": professor["user"]["id"], "content": "سلام"},
        headers=other_student["headers"],
    )
    assert r.status_code == 403


def test_listing_messages_marks_them_as_read(client, professor, student, approved_project):
    client.post(
        f"/api/projects/{approved_project['id']}/messages",
        data={"recipient_id": student["user"]["id"], "content": "سلام"},
        headers=professor["headers"],
    )
    r = client.get(
        f"/api/projects/{approved_project['id']}/messages", headers=student["headers"]
    )
    assert r.status_code == 200
    assert r.json()[0]["read_at"] is not None


def test_download_message_attachment(client, student, professor, approved_project):
    files = {"file": ("note.txt", b"attachment body", "text/plain")}
    r = client.post(
        f"/api/projects/{approved_project['id']}/messages",
        data={"recipient_id": professor["user"]["id"]},
        files=files,
        headers=student["headers"],
    )
    message_id = r.json()["id"]

    r2 = client.get(f"/api/messages/{message_id}/download", headers=professor["headers"])
    assert r2.status_code == 200
    assert r2.content == b"attachment body"


def test_outsider_cannot_download_message_attachment(
    client, student, professor, other_student, approved_project
):
    files = {"file": ("note.txt", b"secret body", "text/plain")}
    r = client.post(
        f"/api/projects/{approved_project['id']}/messages",
        data={"recipient_id": professor["user"]["id"]},
        files=files,
        headers=student["headers"],
    )
    message_id = r.json()["id"]

    r2 = client.get(
        f"/api/messages/{message_id}/download", headers=other_student["headers"]
    )
    assert r2.status_code == 403
