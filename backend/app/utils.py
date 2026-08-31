from sqlalchemy.orm import Session

from .models import Notification, NotificationCategory


def notify(
    db: Session,
    user_id: int,
    content: str,
    link: str | None = None,
    project_id: int | None = None,
    category: NotificationCategory | None = None,
) -> None:
    db.add(
        Notification(
            user_id=user_id,
            content=content,
            link=link,
            project_id=project_id,
            category=category,
        )
    )
