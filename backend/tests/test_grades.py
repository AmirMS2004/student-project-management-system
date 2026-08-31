def test_professor_can_add_grade(client, professor, approved_project):
    r = client.post(
        f"/api/projects/{approved_project['id']}/grades",
        json={"stage": "پروپوزال", "score": 90, "comment": "خوب بود"},
        headers=professor["headers"],
    )
    assert r.status_code == 201
    assert r.json()["score"] == 90


def test_student_cannot_add_grade(client, student, approved_project):
    r = client.post(
        f"/api/projects/{approved_project['id']}/grades",
        json={"stage": "پروپوزال", "score": 90},
        headers=student["headers"],
    )
    assert r.status_code == 403


def test_score_out_of_range_is_rejected(client, professor, approved_project):
    r = client.post(
        f"/api/projects/{approved_project['id']}/grades",
        json={"stage": "پروپوزال", "score": 150},
        headers=professor["headers"],
    )
    assert r.status_code == 422


def test_both_member_roles_can_list_grades(client, professor, student, approved_project):
    client.post(
        f"/api/projects/{approved_project['id']}/grades",
        json={"stage": "پروپوزال", "score": 90},
        headers=professor["headers"],
    )
    r = client.get(
        f"/api/projects/{approved_project['id']}/grades", headers=student["headers"]
    )
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_outsider_cannot_list_grades(client, other_student, approved_project):
    r = client.get(
        f"/api/projects/{approved_project['id']}/grades", headers=other_student["headers"]
    )
    assert r.status_code == 403


def test_resubmitting_same_stage_updates_instead_of_duplicating(
    client, professor, approved_project
):
    r1 = client.post(
        f"/api/projects/{approved_project['id']}/grades",
        json={"stage": "پروپوزال", "score": 70, "comment": "نیاز به اصلاح دارد"},
        headers=professor["headers"],
    )
    assert r1.status_code == 201
    grade_id = r1.json()["id"]

    r2 = client.post(
        f"/api/projects/{approved_project['id']}/grades",
        json={"stage": "پروپوزال", "score": 85, "comment": "اصلاح شد"},
        headers=professor["headers"],
    )
    assert r2.status_code == 200
    assert r2.json()["id"] == grade_id
    assert r2.json()["score"] == 85

    r3 = client.get(
        f"/api/projects/{approved_project['id']}/grades", headers=professor["headers"]
    )
    assert len(r3.json()) == 1


def test_stage_names_are_trimmed_before_comparing(client, professor, approved_project):
    client.post(
        f"/api/projects/{approved_project['id']}/grades",
        json={"stage": "پروپوزال", "score": 70},
        headers=professor["headers"],
    )
    r = client.post(
        f"/api/projects/{approved_project['id']}/grades",
        json={"stage": "  پروپوزال  ", "score": 90},
        headers=professor["headers"],
    )
    assert r.status_code == 200

    all_grades = client.get(
        f"/api/projects/{approved_project['id']}/grades", headers=professor["headers"]
    ).json()
    assert len(all_grades) == 1


def test_different_stages_are_not_merged(client, professor, approved_project):
    client.post(
        f"/api/projects/{approved_project['id']}/grades",
        json={"stage": "پروپوزال", "score": 70},
        headers=professor["headers"],
    )
    client.post(
        f"/api/projects/{approved_project['id']}/grades",
        json={"stage": "دفاع نهایی", "score": 90},
        headers=professor["headers"],
    )
    r = client.get(
        f"/api/projects/{approved_project['id']}/grades", headers=professor["headers"]
    )
    assert len(r.json()) == 2


def test_project_has_no_average_grade_when_no_grades_exist(
    client, professor, approved_project
):
    r = client.get(f"/api/projects/{approved_project['id']}", headers=professor["headers"])
    body = r.json()
    assert body["average_grade"] is None
    assert body["grade_count"] == 0


def test_project_average_grade_reflects_all_stages(client, professor, approved_project):
    client.post(
        f"/api/projects/{approved_project['id']}/grades",
        json={"stage": "پروپوزال", "score": 80},
        headers=professor["headers"],
    )
    client.post(
        f"/api/projects/{approved_project['id']}/grades",
        json={"stage": "دفاع نهایی", "score": 90},
        headers=professor["headers"],
    )
    r = client.get(f"/api/projects/{approved_project['id']}", headers=professor["headers"])
    body = r.json()
    assert body["grade_count"] == 2
    assert body["average_grade"] == 85.0


def test_updating_a_stage_recalculates_the_average(client, professor, approved_project):
    client.post(
        f"/api/projects/{approved_project['id']}/grades",
        json={"stage": "پروپوزال", "score": 60},
        headers=professor["headers"],
    )
    client.post(
        f"/api/projects/{approved_project['id']}/grades",
        json={"stage": "پروپوزال", "score": 100},
        headers=professor["headers"],
    )
    r = client.get(f"/api/projects/{approved_project['id']}", headers=professor["headers"])
    body = r.json()
    assert body["grade_count"] == 1
    assert body["average_grade"] == 100.0
