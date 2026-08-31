"""24-hours-before reminder notifications for calendar events (meetings,
project defense dates, weekly report deadlines).

`check_and_send_reminders(db)` is the testable core: given a DB session, it
scans every project once, and for any event landing in the next 24 hours that
hasn't already been notified (tracked via ReminderLog.event_key), creates a
Notification for the relevant user(s). `reminder_loop()` is the production
wrapper that runs this on a timer, using its own DB session — started once
from a FastAPI startup hook, not exercised in tests.
"""

import asyncio
import logging
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from .calendar_events import next_report_occurrence
from .database import SessionLocal
from .models import Meeting, NotificationCategory, Project, ReminderLog
from .utils import notify

logger = logging.getLogger(__name__)

CHECK_INTERVAL_SECONDS = 15 * 60
REMINDER_WINDOW = timedelta(hours=24)


def _already_sent(db: Session, event_key: str) -> bool:
    return db.query(ReminderLog).filter(ReminderLog.event_key == event_key).first() is not None


def _mark_sent(db: Session, event_key: str) -> None:
    db.add(ReminderLog(event_key=event_key))


def check_and_send_reminders(db: Session, now: datetime | None = None) -> int:
    """Sends any due reminders and returns how many were sent."""
    now = now or datetime.utcnow()
    window_end = now + REMINDER_WINDOW
    sent_count = 0

    # Meetings happening within the next 24 hours.
    meetings = (
        db.query(Meeting)
        .filter(Meeting.scheduled_at > now, Meeting.scheduled_at <= window_end)
        .all()
    )
    for meeting in meetings:
        key = f"meeting:{meeting.id}"
        if _already_sent(db, key):
            continue
        project = meeting.project
        content = f'یادآوری: جلسه پروژه «{project.title}» فردا برگزار می‌شود'
        link = f"/projects/{project.id}"
        notify(db, project.professor_id, content, link=link, project_id=project.id, category=NotificationCategory.MEETING)
        if project.student_id:
            notify(db, project.student_id, content, link=link, project_id=project.id, category=NotificationCategory.MEETING)
        _mark_sent(db, key)
        sent_count += 1

    # Defense dates within the next 24 hours.
    projects_with_defense = (
        db.query(Project)
        .filter(Project.defense_date.isnot(None))
        .filter(Project.defense_date > now, Project.defense_date <= window_end)
        .all()
    )
    for project in projects_with_defense:
        key = f"defense:{project.id}"
        if _already_sent(db, key):
            continue
        content = f'یادآوری: جلسه دفاع پروژه «{project.title}» فردا برگزار می‌شود'
        link = f"/projects/{project.id}"
        notify(db, project.professor_id, content, link=link, project_id=project.id, category=NotificationCategory.PROJECT)
        if project.student_id:
            notify(db, project.student_id, content, link=link, project_id=project.id, category=NotificationCategory.PROJECT)
        _mark_sent(db, key)
        sent_count += 1

    # Weekly report deadlines within the next 24 hours.
    projects_with_deadline = (
        db.query(Project)
        .filter(Project.report_weekday.isnot(None))
        .filter(Project.student_id.isnot(None))
        .all()
    )
    for project in projects_with_deadline:
        occurs_at = next_report_occurrence(project, now)
        if occurs_at is None or occurs_at > window_end:
            continue
        key = f"report:{project.id}:{occurs_at.date().isoformat()}"
        if _already_sent(db, key):
            continue
        content = f'یادآوری: موعد ارسال گزارش هفتگی پروژه «{project.title}» فردا است'
        notify(
            db,
            project.student_id,
            content,
            link=f"/projects/{project.id}",
            project_id=project.id,
            category=NotificationCategory.REPORT,
        )
        _mark_sent(db, key)
        sent_count += 1

    db.commit()
    return sent_count


async def reminder_loop():
    while True:
        try:
            db = SessionLocal()
            try:
                check_and_send_reminders(db)
            finally:
                db.close()
        except Exception:
            logger.exception("Reminder check failed")
        await asyncio.sleep(CHECK_INTERVAL_SECONDS)
