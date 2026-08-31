from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from .. import schemas
from ..access import ensure_project_member, get_project_or_404
from ..auth import get_current_user
from ..database import get_db
from ..file_storage import build_download_response, save_upload
from ..models import FileCategory, NotificationCategory, ProjectFile, User, UserRole
from ..utils import notify

router = APIRouter(prefix="/api", tags=["files"])


@router.post(
    "/projects/{project_id}/files",
    response_model=schemas.ProjectFileOut,
    status_code=status.HTTP_201_CREATED,
)
async def upload_file(
    project_id: int,
    file: UploadFile = File(...),
    description: str = Form(""),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = get_project_or_404(db, project_id)
    ensure_project_member(project, current_user)

    category = (
        FileCategory.REQUIRED
        if current_user.role == UserRole.PROFESSOR
        else FileCategory.SUBMISSION
    )
    original_name, stored_name = await save_upload(file)

    record = ProjectFile(
        project_id=project.id,
        uploaded_by_id=current_user.id,
        category=category,
        original_filename=original_name,
        stored_filename=stored_name,
        description=description or None,
    )
    db.add(record)

    recipient_id = (
        project.student_id if current_user.role == UserRole.PROFESSOR else project.professor_id
    )
    if recipient_id:
        notify(
            db,
            recipient_id,
            f'فایل جدید "{original_name}" در پروژه "{project.title}" بارگذاری شد',
            link=f"/projects/{project.id}",
            project_id=project.id,
            category=NotificationCategory.FILE,
        )

    db.commit()
    db.refresh(record)
    return record


@router.get("/projects/{project_id}/files", response_model=list[schemas.ProjectFileOut])
def list_files(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = get_project_or_404(db, project_id)
    ensure_project_member(project, current_user)

    return (
        db.query(ProjectFile)
        .filter(ProjectFile.project_id == project_id)
        .order_by(ProjectFile.uploaded_at.desc())
        .all()
    )


@router.get("/files/{file_id}/download")
def download_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    record = db.query(ProjectFile).filter(ProjectFile.id == file_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="فایل یافت نشد")
    project = get_project_or_404(db, record.project_id)
    ensure_project_member(project, current_user)

    return build_download_response(record.stored_filename, record.original_filename)
