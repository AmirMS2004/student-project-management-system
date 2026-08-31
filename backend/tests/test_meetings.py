def test_professor_can_schedule_meeting(client, professor, approved_project):
    r = client.post(
        f"/api/projects/{approved_project['id']}/meetings",
        json={"scheduled_at": "2030-01-01T10:00:00", "location": "آنلاین"},
        headers=professor["headers"],
    )
    assert r.status_code == 201
    assert r.json()["location"] == "آنلاین"


def test_student_cannot_schedule_meeting(client, student, approved_project):
    r = client.post(
        f"/api/projects/{approved_project['id']}/meetings",
        json={"scheduled_at": "2030-01-01T10:00:00"},
        headers=student["headers"],
    )
    assert r.status_code == 403


def test_both_member_roles_can_list_meetings(client, professor, student, approved_project):
    client.post(
        f"/api/projects/{approved_project['id']}/meetings",
        json={"scheduled_at": "2030-01-01T10:00:00"},
        headers=professor["headers"],
    )
    r_prof = client.get(
        f"/api/projects/{approved_project['id']}/meetings", headers=professor["headers"]
    )
    r_stud = client.get(
        f"/api/projects/{approved_project['id']}/meetings", headers=student["headers"]
    )
    assert r_prof.status_code == 200 and len(r_prof.json()) == 1
    assert r_stud.status_code == 200 and len(r_stud.json()) == 1


def test_outsider_cannot_list_meetings(client, other_student, approved_project):
    r = client.get(
        f"/api/projects/{approved_project['id']}/meetings", headers=other_student["headers"]
    )
    assert r.status_code == 403


def test_professor_can_add_report_to_meeting(client, professor, approved_project):
    r = client.post(
        f"/api/projects/{approved_project['id']}/meetings",
        json={"scheduled_at": "2030-01-01T10:00:00"},
        headers=professor["headers"],
    )
    meeting_id = r.json()["id"]

    r2 = client.patch(
        f"/api/meetings/{meeting_id}",
        json={"report": "جلسه با موفقیت برگزار شد"},
        headers=professor["headers"],
    )
    assert r2.status_code == 200
    assert r2.json()["report"] == "جلسه با موفقیت برگزار شد"


def test_assigned_student_can_propose_meeting(client, student, approved_project):
    r = client.post(
        f"/api/projects/{approved_project['id']}/meeting-requests",
        json={"scheduled_at": "2030-01-01T10:00:00", "location": "آنلاین", "message": "این زمان خوبه؟"},
        headers=student["headers"],
    )
    assert r.status_code == 201
    body = r.json()
    assert body["status"] == "pending"
    assert body["location"] == "آنلاین"


def test_professor_cannot_propose_meeting(client, professor, approved_project):
    r = client.post(
        f"/api/projects/{approved_project['id']}/meeting-requests",
        json={"scheduled_at": "2030-01-01T10:00:00"},
        headers=professor["headers"],
    )
    assert r.status_code == 403


def test_unrelated_student_cannot_propose_meeting_for_others_project(
    client, other_student, approved_project
):
    r = client.post(
        f"/api/projects/{approved_project['id']}/meeting-requests",
        json={"scheduled_at": "2030-01-01T10:00:00"},
        headers=other_student["headers"],
    )
    assert r.status_code == 403


def test_professor_approving_meeting_request_creates_meeting(
    client, professor, student, approved_project
):
    r = client.post(
        f"/api/projects/{approved_project['id']}/meeting-requests",
        json={"scheduled_at": "2030-01-01T10:00:00", "location": "اتاق 3"},
        headers=student["headers"],
    )
    request_id = r.json()["id"]

    r2 = client.patch(
        f"/api/meeting-requests/{request_id}",
        json={"approve": True},
        headers=professor["headers"],
    )
    assert r2.status_code == 200
    assert r2.json()["status"] == "approved"

    meetings = client.get(
        f"/api/projects/{approved_project['id']}/meetings", headers=professor["headers"]
    ).json()
    assert len(meetings) == 1
    assert meetings[0]["location"] == "اتاق 3"


def test_professor_rejecting_meeting_request_does_not_create_meeting(
    client, professor, student, approved_project
):
    r = client.post(
        f"/api/projects/{approved_project['id']}/meeting-requests",
        json={"scheduled_at": "2030-01-01T10:00:00"},
        headers=student["headers"],
    )
    request_id = r.json()["id"]

    r2 = client.patch(
        f"/api/meeting-requests/{request_id}",
        json={"approve": False},
        headers=professor["headers"],
    )
    assert r2.status_code == 200
    assert r2.json()["status"] == "rejected"

    meetings = client.get(
        f"/api/projects/{approved_project['id']}/meetings", headers=professor["headers"]
    ).json()
    assert meetings == []


def test_student_cannot_decide_meeting_request(client, student, approved_project):
    r = client.post(
        f"/api/projects/{approved_project['id']}/meeting-requests",
        json={"scheduled_at": "2030-01-01T10:00:00"},
        headers=student["headers"],
    )
    request_id = r.json()["id"]

    r2 = client.patch(
        f"/api/meeting-requests/{request_id}",
        json={"approve": True},
        headers=student["headers"],
    )
    assert r2.status_code == 403


def test_cannot_decide_meeting_request_twice(client, professor, student, approved_project):
    r = client.post(
        f"/api/projects/{approved_project['id']}/meeting-requests",
        json={"scheduled_at": "2030-01-01T10:00:00"},
        headers=student["headers"],
    )
    request_id = r.json()["id"]
    client.patch(
        f"/api/meeting-requests/{request_id}",
        json={"approve": True},
        headers=professor["headers"],
    )

    r2 = client.patch(
        f"/api/meeting-requests/{request_id}",
        json={"approve": False},
        headers=professor["headers"],
    )
    assert r2.status_code == 400
