from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from .. import schemas
from ..access import ensure_project_owner
from ..auth import get_current_user, require_professor
from ..database import get_db
from ..file_storage import build_download_response, save_upload
from ..models import NotificationCategory, Project, ProjectStatus, User, UserRole
from ..pdf_export import PersianFontNotFoundError, build_project_pdf
from ..utils import notify
from ..zip_export import build_project_zip

router = APIRouter(prefix="/api/projects", tags=["projects"])


def _project_query(db: Session):
    return db.query(Project).options(
        joinedload(Project.professor), joinedload(Project.student)
    )


@router.get("", response_model=list[schemas.ProjectOut])
def list_projects(
    status_filter: Optional[ProjectStatus] = None,
    mine: bool = False,
    professor_id: Optional[int] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = _project_query(db)

    if current_user.role == UserRole.PROFESSOR:
        if mine:
            query = query.filter(Project.professor_id == current_user.id)
    elif current_user.role == UserRole.STUDENT:
        if mine:
            query = query.filter(Project.student_id == current_user.id)
        else:
            # students may browse open projects plus their own assignment history
            query = query.filter(
                (Project.status == ProjectStatus.OPEN)
                | (Project.student_id == current_user.id)
            )
    # admins see every project regardless of `mine` (they aren't attached to any)

    if professor_id:
        query = query.filter(Project.professor_id == professor_id)

    if search:
        pattern = f"%{search.strip()}%"
        query = query.filter(
            or_(Project.title.ilike(pattern), Project.abstract.ilike(pattern))
        )

    if status_filter:
        query = query.filter(Project.status == status_filter)

    return query.order_by(Project.created_at.desc()).all()


@router.post("", response_model=schemas.ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: schemas.ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_professor),
):
    project = Project(
        title=payload.title,
        abstract=payload.abstract,
        professor_id=current_user.id,
        status=ProjectStatus.OPEN,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def _get_project_or_404(db: Session, project_id: int) -> Project:
    project = _project_query(db).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="پروژه یافت نشد")
    return project


def _ensure_can_view(project: Project, current_user: User):
    if current_user.role == UserRole.ADMIN:
        return
    if current_user.role == UserRole.PROFESSOR:
        if project.professor_id != current_user.id:
            raise HTTPException(status_code=403, detail="دسترسی غیرمجاز")
    else:
        allowed = (
            project.status == ProjectStatus.OPEN
            or project.student_id == current_user.id
        )
        if not allowed:
            raise HTTPException(status_code=403, detail="دسترسی غیرمجاز")


@router.get("/{project_id}", response_model=schemas.ProjectOut)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = _get_project_or_404(db, project_id)
    _ensure_can_view(project, current_user)
    return project


@router.patch("/{project_id}", response_model=schemas.ProjectOut)
def update_project(
    project_id: int,
    payload: schemas.ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_professor),
):
    project = _get_project_or_404(db, project_id)
    ensure_project_owner(project, current_user)

    data = payload.model_dump(exclude_unset=True)
    defense_date_changed = (
        "defense_date" in data and data["defense_date"] != project.defense_date
    )
    for key, value in data.items():
        setattr(project, key, value)

    if defense_date_changed and project.student_id:
        notify(
            db,
            project.student_id,
            f'تاریخ دفاع پروژه "{project.title}" ثبت/به‌روزرسانی شد',
            link=f"/projects/{project.id}",
            project_id=project.id,
            category=NotificationCategory.PROJECT,
        )

    db.commit()
    db.refresh(project)
    return project


@router.post("/{project_id}/brief-file", response_model=schemas.ProjectOut)
async def upload_brief_file(
    project_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_professor),
):
    project = _get_project_or_404(db, project_id)
    ensure_project_owner(project, current_user)

    original_name, stored_name = await save_upload(file)
    project.brief_original_filename = original_name
    project.brief_stored_filename = stored_name

    db.commit()
    db.refresh(project)
    return project


@router.get("/{project_id}/brief-file/download")
def download_brief_file(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = _get_project_or_404(db, project_id)
    _ensure_can_view(project, current_user)

    return build_download_response(
        project.brief_stored_filename, project.brief_original_filename
    )


@router.get("/{project_id}/export-pdf")
def export_project_pdf(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = _get_project_or_404(db, project_id)
    _ensure_can_view(project, current_user)

    try:
        pdf_buffer = build_project_pdf(project)
    except PersianFontNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    filename = f"project-{project.id}-dossier.pdf"
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{project_id}/export-zip")
def export_project_zip(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = _get_project_or_404(db, project_id)
    _ensure_can_view(project, current_user)

    try:
        zip_buffer = build_project_zip(project)
    except PersianFontNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    filename = f"project-{project.id}-archive.zip"
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_professor),
):
    project = _get_project_or_404(db, project_id)
    ensure_project_owner(project, current_user)
    if project.student_id is not None:
        raise HTTPException(
            status_code=400, detail="پروژه‌ای که دانشجو دارد قابل حذف نیست"
        )
    db.delete(project)
    db.commit()
