def test_student_can_request_open_project(client, student, open_project):
    r = client.post(
        f"/api/projects/{open_project['id']}/requests",
        json={"message": "علاقه‌مندم"},
        headers=student["headers"],
    )
    assert r.status_code == 201
    assert r.json()["status"] == "pending"


def test_cannot_request_same_project_twice_while_pending(client, student, open_project):
    client.post(
        f"/api/projects/{open_project['id']}/requests",
        json={},
        headers=student["headers"],
    )
    r = client.post(
        f"/api/projects/{open_project['id']}/requests",
        json={},
        headers=student["headers"],
    )
    assert r.status_code == 400


def test_cannot_request_non_open_project(client, other_student, approved_project):
    r = client.post(
        f"/api/projects/{approved_project['id']}/requests",
        json={},
        headers=other_student["headers"],
    )
    assert r.status_code == 400


def test_only_owner_professor_can_list_requests(client, register_user, student, open_project):
    client.post(
        f"/api/projects/{open_project['id']}/requests", json={}, headers=student["headers"]
    )
    other_prof = register_user(
        role="professor", email="other-prof4@test.com", phone_number="09300000004"
    )
    r = client.get(
        f"/api/projects/{open_project['id']}/requests", headers=other_prof["headers"]
    )
    assert r.status_code == 403


def test_approving_a_request_assigns_the_student(client, professor, student, open_project):
    r = client.post(
        f"/api/projects/{open_project['id']}/requests", json={}, headers=student["headers"]
    )
    request_id = r.json()["id"]

    r2 = client.patch(
        f"/api/requests/{request_id}", json={"approve": True}, headers=professor["headers"]
    )
    assert r2.status_code == 200
    assert r2.json()["status"] == "approved"

    r3 = client.get(f"/api/projects/{open_project['id']}", headers=professor["headers"])
    project = r3.json()
    assert project["status"] == "in_progress"
    assert project["student_id"] == student["user"]["id"]


def test_approving_one_request_auto_rejects_other_pending_requests(
    client, professor, student, other_student, open_project
):
    r1 = client.post(
        f"/api/projects/{open_project['id']}/requests", json={}, headers=student["headers"]
    )
    r2 = client.post(
        f"/api/projects/{open_project['id']}/requests",
        json={},
        headers=other_student["headers"],
    )
    request1_id, request2_id = r1.json()["id"], r2.json()["id"]

    client.patch(
        f"/api/requests/{request1_id}", json={"approve": True}, headers=professor["headers"]
    )

    r = client.get("/api/requests/mine", headers=other_student["headers"])
    other_requests = [x for x in r.json() if x["id"] == request2_id]
    assert other_requests[0]["status"] == "rejected"


def test_rejecting_a_request_keeps_project_open(client, professor, student, open_project):
    r = client.post(
        f"/api/projects/{open_project['id']}/requests", json={}, headers=student["headers"]
    )
    request_id = r.json()["id"]

    client.patch(
        f"/api/requests/{request_id}", json={"approve": False}, headers=professor["headers"]
    )

    r2 = client.get(f"/api/projects/{open_project['id']}", headers=professor["headers"])
    assert r2.json()["status"] == "open"
    assert r2.json()["student_id"] is None


def test_cannot_decide_an_already_decided_request(client, professor, student, open_project):
    r = client.post(
        f"/api/projects/{open_project['id']}/requests", json={}, headers=student["headers"]
    )
    request_id = r.json()["id"]
    client.patch(
        f"/api/requests/{request_id}", json={"approve": True}, headers=professor["headers"]
    )

    r2 = client.patch(
        f"/api/requests/{request_id}", json={"approve": False}, headers=professor["headers"]
    )
    assert r2.status_code == 400


def test_student_can_see_own_request_history(client, student, open_project):
    client.post(f"/api/projects/{open_project['id']}/requests", json={}, headers=student["headers"])
    r = client.get("/api/requests/mine", headers=student["headers"])
    assert r.status_code == 200
    assert len(r.json()) == 1
