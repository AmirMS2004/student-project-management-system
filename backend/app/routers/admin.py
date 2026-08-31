from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import schemas
from ..auth import require_admin
from ..database import get_db
from ..models import Project, ProjectStatus, User, UserRole
from ..settings import get_professor_invite_code, set_professor_invite_code

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/stats", response_model=schemas.AdminStats)
def get_admin_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    projects = db.query(Project).all()

    total = len(projects)
    open_count = sum(1 for p in projects if p.status == ProjectStatus.OPEN)
    active = sum(1 for p in projects if p.status == ProjectStatus.IN_PROGRESS)
    completed = sum(1 for p in projects if p.status == ProjectStatus.COMPLETED)

    durations = [
        (p.end_date - p.start_date).days
        for p in projects
        if p.start_date and p.end_date
    ]
    avg_duration = sum(durations) / len(durations) if durations else None
    avg_progress = sum(p.progress_percent for p in projects) / total if total else 0.0

    total_professors = db.query(User).filter(User.role == UserRole.PROFESSOR).count()
    total_students = db.query(User).filter(User.role == UserRole.STUDENT).count()

    return schemas.AdminStats(
        total_projects=total,
        open_projects=open_count,
        active_projects=active,
        completed_projects=completed,
        average_duration_days=avg_duration,
        average_progress_percent=round(avg_progress, 1),
        total_professors=total_professors,
        total_students=total_students,
    )


@router.get("/users", response_model=list[schemas.UserOut])
def list_all_users(
    role: Optional[UserRole] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    query = db.query(User)
    if role:
        query = query.filter(User.role == role)
    return query.order_by(User.created_at.desc()).all()


@router.get("/settings", response_model=schemas.AdminSettingsOut)
def get_admin_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    return schemas.AdminSettingsOut(professor_invite_code=get_professor_invite_code(db))


@router.patch("/settings", response_model=schemas.AdminSettingsOut)
def update_admin_settings(
    payload: schemas.AdminSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    set_professor_invite_code(db, payload.professor_invite_code.strip())
    db.commit()
    return schemas.AdminSettingsOut(professor_invite_code=get_professor_invite_code(db))
