from datetime import datetime, timedelta


def test_professor_calendar_shows_own_meeting_and_defense(
    client, professor, approved_project
):
    scheduled_at = (datetime.utcnow() + timedelta(days=2)).isoformat()
    client.post(
        f"/api/projects/{approved_project['id']}/meetings",
        json={"scheduled_at": scheduled_at, "location": "اتاق 101"},
        headers=professor["headers"],
    )
    defense_at = (datetime.utcnow() + timedelta(days=10)).isoformat()
    client.patch(
        f"/api/projects/{approved_project['id']}",
        json={"defense_date": defense_at},
        headers=professor["headers"],
    )

    r = client.get("/api/calendar/events", headers=professor["headers"])
    assert r.status_code == 200
    events = r.json()
    types = {e["event_type"] for e in events}
    assert "meeting" in types
    assert "defense" in types
    assert all(e["project_id"] == approved_project["id"] for e in events)


def test_professor_calendar_never_includes_report_deadline(
    client, professor, approved_project
):
    client.patch(
        f"/api/projects/{approved_project['id']}",
        json={"report_weekday": 6, "report_deadline_time": "23:59"},
        headers=professor["headers"],
    )
    r = client.get("/api/calendar/events", headers=professor["headers"])
    assert r.status_code == 200
    types = {e["event_type"] for e in r.json()}
    assert "report_deadline" not in types


def test_student_calendar_shows_meeting_defense_and_report_deadline(
    client, professor, student, approved_project
):
    scheduled_at = (datetime.utcnow() + timedelta(days=2)).isoformat()
    client.post(
        f"/api/projects/{approved_project['id']}/meetings",
        json={"scheduled_at": scheduled_at, "location": "آنلاین"},
        headers=professor["headers"],
    )
    defense_at = (datetime.utcnow() + timedelta(days=10)).isoformat()
    client.patch(
        f"/api/projects/{approved_project['id']}",
        json={
            "defense_date": defense_at,
            "report_weekday": 6,
            "report_deadline_time": "23:59",
        },
        headers=professor["headers"],
    )

    r = client.get("/api/calendar/events", headers=student["headers"])
    assert r.status_code == 200
    events = r.json()
    types = {e["event_type"] for e in events}
    assert types == {"meeting", "defense", "report_deadline"}
    # events must come back sorted chronologically
    occurs_ats = [e["occurs_at"] for e in events]
    assert occurs_ats == sorted(occurs_ats)


def test_calendar_excludes_unrelated_projects(
    client, professor, student, other_student, approved_project
):
    r = client.get("/api/calendar/events", headers=other_student["headers"])
    assert r.status_code == 200
    assert r.json() == []


def test_report_deadline_requires_no_special_action_when_unset(client, student, open_project):
    r = client.get("/api/calendar/events", headers=student["headers"])
    assert r.status_code == 200
    assert r.json() == []
