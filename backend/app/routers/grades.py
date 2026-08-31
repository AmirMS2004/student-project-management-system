from datetime import datetime

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from .. import schemas
from ..access import ensure_project_member, ensure_project_owner, get_project_or_404
from ..auth import get_current_user, require_professor
from ..database import get_db
from ..models import Grade, NotificationCategory, User
from ..utils import notify

router = APIRouter(prefix="/api", tags=["grades"])


@router.post(
    "/projects/{project_id}/grades",
    response_model=schemas.GradeOut,
    status_code=status.HTTP_201_CREATED,
)
def add_grade(
    project_id: int,
    payload: schemas.GradeCreate,
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_professor),
):
    project = get_project_or_404(db, project_id)
    ensure_project_owner(project, current_user)

    stage = payload.stage.strip()

    # Consolidate grades by stage: re-submitting the same stage updates the
    # existing record instead of creating a duplicate row.
    grade = (
        db.query(Grade)
        .filter(Grade.project_id == project.id, Grade.stage == stage)
        .first()
    )
    is_update = grade is not None
    if grade:
        grade.score = payload.score
        grade.comment = payload.comment
        grade.graded_at = datetime.utcnow()
    else:
        grade = Grade(
            project_id=project.id,
            stage=stage,
            score=payload.score,
            comment=payload.comment,
        )
        db.add(grade)

    response.status_code = status.HTTP_200_OK if is_update else status.HTTP_201_CREATED

    if project.student_id:
        verb = "به‌روزرسانی" if is_update else "ثبت"
        notify(
            db,
            project.student_id,
            f'نمره مرحله "{stage}" برای پروژه "{project.title}" {verb} شد',
            link=f"/projects/{project.id}",
            project_id=project.id,
            category=NotificationCategory.GRADE,
        )

    db.commit()
    db.refresh(grade)
    return grade


@router.get("/projects/{project_id}/grades", response_model=list[schemas.GradeOut])
def list_grades(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = get_project_or_404(db, project_id)
    ensure_project_member(project, current_user)

    return (
        db.query(Grade)
        .filter(Grade.project_id == project_id)
        .order_by(Grade.graded_at.desc())
        .all()
    )
