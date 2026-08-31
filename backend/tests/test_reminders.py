from datetime import datetime, timedelta

from app.models import ReminderLog
from app.reminders import check_and_send_reminders


def test_meeting_reminder_sent_to_both_and_not_duplicated(
    client, db_session, professor, student, approved_project
):
    scheduled_at = (datetime.utcnow() + timedelta(hours=20)).isoformat()
    client.post(
        f"/api/projects/{approved_project['id']}/meetings",
        json={"scheduled_at": scheduled_at, "location": "اتاق 101"},
        headers=professor["headers"],
    )

    db = db_session()
    try:
        sent = check_and_send_reminders(db)
        assert sent == 1
        assert db.query(ReminderLog).count() == 1
    finally:
        db.close()

    prof_notifs = client.get("/api/notifications", headers=professor["headers"]).json()
    student_notifs = client.get("/api/notifications", headers=student["headers"]).json()
    assert any("جلسه" in n["content"] for n in prof_notifs)
    assert any("جلسه" in n["content"] for n in student_notifs)

    # Running again must not re-notify for the same meeting.
    db = db_session()
    try:
        sent_again = check_and_send_reminders(db)
        assert sent_again == 0
    finally:
        db.close()


def test_meeting_outside_24h_window_not_reminded(
    client, db_session, professor, approved_project
):
    scheduled_at = (datetime.utcnow() + timedelta(days=5)).isoformat()
    client.post(
        f"/api/projects/{approved_project['id']}/meetings",
        json={"scheduled_at": scheduled_at, "location": "اتاق 101"},
        headers=professor["headers"],
    )

    db = db_session()
    try:
        sent = check_and_send_reminders(db)
        assert sent == 0
    finally:
        db.close()


def test_defense_reminder_sent_to_both_roles(
    client, db_session, professor, student, approved_project
):
    defense_at = (datetime.utcnow() + timedelta(hours=10)).isoformat()
    client.patch(
        f"/api/projects/{approved_project['id']}",
        json={"defense_date": defense_at},
        headers=professor["headers"],
    )

    db = db_session()
    try:
        sent = check_and_send_reminders(db)
        assert sent == 1
    finally:
        db.close()

    prof_notifs = client.get("/api/notifications", headers=professor["headers"]).json()
    student_notifs = client.get("/api/notifications", headers=student["headers"]).json()
    assert any("دفاع" in n["content"] for n in prof_notifs)
    assert any("دفاع" in n["content"] for n in student_notifs)


def test_report_deadline_reminder_sent_only_to_student(
    client, db_session, professor, student, approved_project
):
    target = datetime.utcnow() + timedelta(hours=2)
    client.patch(
        f"/api/projects/{approved_project['id']}",
        json={
            "report_weekday": target.weekday(),
            "report_deadline_time": target.strftime("%H:%M"),
        },
        headers=professor["headers"],
    )

    db = db_session()
    try:
        sent = check_and_send_reminders(db)
        assert sent == 1
    finally:
        db.close()

    prof_notifs = client.get("/api/notifications", headers=professor["headers"]).json()
    student_notifs = client.get("/api/notifications", headers=student["headers"]).json()
    assert not any("گزارش هفتگی" in n["content"] for n in prof_notifs)
    assert any("گزارش هفتگی" in n["content"] for n in student_notifs)
