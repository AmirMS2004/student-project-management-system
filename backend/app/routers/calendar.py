from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import schemas
from ..auth import get_current_user
from ..calendar_events import get_calendar_events
from ..database import get_db
from ..models import User

router = APIRouter(prefix="/api/calendar", tags=["calendar"])


@router.get("/events", response_model=list[schemas.CalendarEventOut])
def list_calendar_events(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    events = get_calendar_events(db, current_user)
    return [
        schemas.CalendarEventOut(
            event_type=e.event_type,
            title=e.title,
            occurs_at=e.occurs_at,
            project_id=e.project_id,
            project_title=e.project_title,
            extra=e.extra,
        )
        for e in events
    ]
