def test_dashboard_stats_for_professor_with_no_projects(client, professor):
    r = client.get("/api/dashboard/stats", headers=professor["headers"])
    assert r.status_code == 200
    body = r.json()
    assert body["total_projects"] == 0
    assert body["active_projects"] == 0
    assert body["completed_projects"] == 0


def test_dashboard_stats_reflects_projects(client, professor, approved_project):
    r = client.get("/api/dashboard/stats", headers=professor["headers"])
    assert r.status_code == 200
    body = r.json()
    assert body["total_projects"] == 1
    assert body["active_projects"] == 1
    assert body["completed_projects"] == 0


def test_student_cannot_access_dashboard_stats(client, student):
    r = client.get("/api/dashboard/stats", headers=student["headers"])
    assert r.status_code == 403


def test_dashboard_only_counts_own_projects(client, professor, register_user, approved_project):
    other_prof = register_user(
        role="professor", email="other-prof6@test.com", phone_number="09300000006"
    )
    r = client.get("/api/dashboard/stats", headers=other_prof["headers"])
    assert r.json()["total_projects"] == 0
