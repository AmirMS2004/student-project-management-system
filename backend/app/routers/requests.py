from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from .. import schemas
from ..access import ensure_project_owner, get_project_or_404
from ..auth import require_professor, require_student
from ..database import get_db
from ..models import (
    NotificationCategory,
    ProjectRequest,
    ProjectStatus,
    RequestStatus,
    User,
)
from ..utils import notify

router = APIRouter(prefix="/api", tags=["project-requests"])


@router.post(
    "/projects/{project_id}/requests",
    response_model=schemas.ProjectRequestOut,
    status_code=status.HTTP_201_CREATED,
)
def request_project(
    project_id: int,
    payload: schemas.ProjectRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student),
):
    project = get_project_or_404(db, project_id)
    if project.status != ProjectStatus.OPEN:
        raise HTTPException(status_code=400, detail="این پروژه در حال حاضر قابل انتخاب نیست")

    existing = (
        db.query(ProjectRequest)
        .filter(
            ProjectRequest.project_id == project_id,
            ProjectRequest.student_id == current_user.id,
            ProjectRequest.status == RequestStatus.PENDING,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="درخواست شما قبلا ثبت شده است")

    req = ProjectRequest(
        project_id=project_id,
        student_id=current_user.id,
        message=payload.message,
    )
    db.add(req)

    notify(
        db,
        project.professor_id,
        f'دانشجوی جدیدی برای پروژه "{project.title}" درخواست داد',
        link=f"/projects/{project.id}",
        project_id=project.id,
        category=NotificationCategory.REQUEST,
    )

    db.commit()
    db.refresh(req)
    return req


@router.get("/projects/{project_id}/requests", response_model=list[schemas.ProjectRequestOut])
def list_project_requests(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_professor),
):
    project = get_project_or_404(db, project_id)
    ensure_project_owner(project, current_user)

    return (
        db.query(ProjectRequest)
        .options(joinedload(ProjectRequest.student))
        .filter(ProjectRequest.project_id == project_id)
        .order_by(ProjectRequest.requested_at.desc())
        .all()
    )


@router.get("/requests/mine", response_model=list[schemas.ProjectRequestOut])
def my_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student),
):
    return (
        db.query(ProjectRequest)
        .options(joinedload(ProjectRequest.project))
        .filter(ProjectRequest.student_id == current_user.id)
        .order_by(ProjectRequest.requested_at.desc())
        .all()
    )


@router.patch("/requests/{request_id}", response_model=schemas.ProjectRequestOut)
def decide_request(
    request_id: int,
    payload: schemas.ProjectRequestDecision,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_professor),
):
    req = (
        db.query(ProjectRequest)
        .options(joinedload(ProjectRequest.project))
        .filter(ProjectRequest.id == request_id)
        .first()
    )
    if not req:
        raise HTTPException(status_code=404, detail="درخواست یافت نشد")

    project = req.project
    ensure_project_owner(project, current_user)
    if req.status != RequestStatus.PENDING:
        raise HTTPException(status_code=400, detail="این درخواست قبلا بررسی شده است")

    req.decided_at = datetime.utcnow()

    if payload.approve:
        if project.status != ProjectStatus.OPEN:
            raise HTTPException(status_code=400, detail="این پروژه دیگر قابل واگذاری نیست")
        req.status = RequestStatus.APPROVED
        project.student_id = req.student_id
        project.status = ProjectStatus.IN_PROGRESS

        # auto-reject any other pending requests for this project
        others = (
            db.query(ProjectRequest)
            .filter(
                ProjectRequest.project_id == project.id,
                ProjectRequest.id != req.id,
                ProjectRequest.status == RequestStatus.PENDING,
            )
            .all()
        )
        for other in others:
            other.status = RequestStatus.REJECTED
            other.decided_at = datetime.utcnow()
            notify(
                db,
                other.student_id,
                f'درخواست شما برای پروژه "{project.title}" رد شد',
                link=f"/projects/{project.id}",
                project_id=project.id,
                category=NotificationCategory.PROJECT,
            )

        notify(
            db,
            req.student_id,
            f'درخواست شما برای پروژه "{project.title}" تایید شد',
            link=f"/projects/{project.id}",
            project_id=project.id,
            category=NotificationCategory.PROJECT,
        )
    else:
        req.status = RequestStatus.REJECTED
        notify(
            db,
            req.student_id,
            f'درخواست شما برای پروژه "{project.title}" رد شد',
            link=f"/projects/{project.id}",
            project_id=project.id,
            category=NotificationCategory.PROJECT,
        )

    db.commit()
    db.refresh(req)
    return req
