"""Builds the list of calendar events for a user (meetings, project defense
dates, and recurring weekly report deadlines), and computes the next
occurrence of a project's weekly report deadline.

Shared between the `/api/calendar/events` endpoint (per-user, forward-looking
list) and the background reminder job (`app/reminders.py`, which scans every
project instead of one user's).
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from .models import Project, User, UserRole


@dataclass
class CalendarEvent:
    event_type: str  # "meeting" | "defense" | "report_deadline"
    title: str
    occurs_at: datetime
    project_id: int
    project_title: str
    extra: Optional[str] = None
    event_key: str = ""


def next_report_occurrence(project: Project, after: datetime) -> Optional[datetime]:
    """Next datetime on/after `after` matching the project's configured
    weekly report-deadline weekday + time, or None if not configured."""
    if project.report_weekday is None:
        return None
    time_str = project.report_deadline_time or "23:59"
    hour, minute = (int(part) for part in time_str.split(":"))

    days_ahead = (project.report_weekday - after.weekday()) % 7
    candidate = (after + timedelta(days=days_ahead)).replace(
        hour=hour, minute=minute, second=0, microsecond=0
    )
    if candidate <= after:
        candidate += timedelta(days=7)
    return candidate


def _report_occurrences_in_window(
    project: Project, start: datetime, end: datetime
) -> list[datetime]:
    occurrences = []
    cursor = start
    while True:
        occ = next_report_occurrence(project, cursor)
        if occ is None or occ > end:
            break
        occurrences.append(occ)
        cursor = occ  # next_report_occurrence always steps forward from here
    return occurrences


def _project_events(
    project: Project, *, include_report_deadline: bool, now: datetime, window_end: datetime
) -> list[CalendarEvent]:
    events = []

    for meeting in project.meetings:
        if window_end >= meeting.scheduled_at >= now - timedelta(days=3):
            events.append(
                CalendarEvent(
                    event_type="meeting",
                    title=f'جلسه پروژه «{project.title}»',
                    occurs_at=meeting.scheduled_at,
                    project_id=project.id,
                    project_title=project.title,
                    extra=meeting.location,
                    event_key=f"meeting:{meeting.id}",
                )
            )

    if project.defense_date and now - timedelta(days=3) <= project.defense_date <= window_end:
        events.append(
            CalendarEvent(
                event_type="defense",
                title=f'جلسه دفاع پروژه «{project.title}»',
                occurs_at=project.defense_date,
                project_id=project.id,
                project_title=project.title,
                event_key=f"defense:{project.id}",
            )
        )

    if include_report_deadline:
        for occ in _report_occurrences_in_window(project, now, window_end):
            events.append(
                CalendarEvent(
                    event_type="report_deadline",
                    title=f'موعد گزارش هفتگی پروژه «{project.title}»',
                    occurs_at=occ,
                    project_id=project.id,
                    project_title=project.title,
                    event_key=f"report:{project.id}:{occ.date().isoformat()}",
                )
            )

    return events


def get_calendar_events(
    db: Session, user: User, *, now: Optional[datetime] = None, window_days: int = 45
) -> list[CalendarEvent]:
    now = now or datetime.utcnow()
    window_end = now + timedelta(days=window_days)

    if user.role == UserRole.PROFESSOR:
        projects = db.query(Project).filter(Project.professor_id == user.id).all()
        include_report_deadline = False
    elif user.role == UserRole.STUDENT:
        projects = db.query(Project).filter(Project.student_id == user.id).all()
        include_report_deadline = True
    else:
        projects = []
        include_report_deadline = False

    events: list[CalendarEvent] = []
    for project in projects:
        events.extend(
            _project_events(
                project,
                include_report_deadline=include_report_deadline,
                now=now,
                window_end=window_end,
            )
        )

    events.sort(key=lambda e: e.occurs_at)
    return events
