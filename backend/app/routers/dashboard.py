from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import schemas
from ..auth import require_professor
from ..database import get_db
from ..models import Project, ProjectStatus, User

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=schemas.DashboardStats)
def get_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_professor),
):
    projects = db.query(Project).filter(Project.professor_id == current_user.id).all()

    total = len(projects)
    active = sum(1 for p in projects if p.status == ProjectStatus.IN_PROGRESS)
    completed = sum(1 for p in projects if p.status == ProjectStatus.COMPLETED)

    durations = [
        (p.end_date - p.start_date).days
        for p in projects
        if p.start_date and p.end_date
    ]
    avg_duration = sum(durations) / len(durations) if durations else None

    avg_progress = sum(p.progress_percent for p in projects) / total if total else 0.0

    return schemas.DashboardStats(
        total_projects=total,
        active_projects=active,
        completed_projects=completed,
        average_duration_days=avg_duration,
        average_progress_percent=round(avg_progress, 1),
    )
