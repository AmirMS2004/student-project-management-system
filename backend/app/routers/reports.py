from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from .. import schemas
from ..access import ensure_project_member, ensure_project_owner, get_project_or_404
from ..auth import get_current_user, require_professor, require_student
from ..database import get_db
from ..file_storage import build_download_response, save_upload
from ..models import NotificationCategory, Report, User
from ..utils import notify

router = APIRouter(prefix="/api", tags=["reports"])


@router.post(
    "/projects/{project_id}/reports",
    response_model=schemas.ReportOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_report(
    project_id: int,
    content: str = Form(...),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student),
):
    project = get_project_or_404(db, project_id)
    if project.student_id != current_user.id:
        raise HTTPException(status_code=403, detail="دسترسی غیرمجاز")

    report = Report(
        project_id=project.id, student_id=current_user.id, content=content
    )

    if file:
        original_name, stored_name = await save_upload(file)
        report.attachment_original_filename = original_name
        report.attachment_stored_filename = stored_name

    db.add(report)

    notify(
        db,
        project.professor_id,
        f'گزارش هفتگی جدید برای پروژه "{project.title}" ثبت شد',
        link=f"/projects/{project.id}",
        project_id=project.id,
        category=NotificationCategory.REPORT,
    )

    db.commit()
    db.refresh(report)
    return report


@router.get("/projects/{project_id}/reports", response_model=list[schemas.ReportOut])
def list_reports(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = get_project_or_404(db, project_id)
    ensure_project_member(project, current_user)

    return (
        db.query(Report)
        .filter(Report.project_id == project_id)
        .order_by(Report.created_at.desc())
        .all()
    )


@router.patch("/reports/{report_id}", response_model=schemas.ReportOut)
def comment_on_report(
    report_id: int,
    payload: schemas.ReportComment,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_professor),
):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="گزارش یافت نشد")
    project = get_project_or_404(db, report.project_id)
    ensure_project_owner(project, current_user)

    report.professor_comment = payload.professor_comment
    report.commented_at = datetime.utcnow()

    notify(
        db,
        report.student_id,
        f'استاد روی گزارش شما در پروژه "{project.title}" نظر ثبت کرد',
        link=f"/projects/{project.id}",
        project_id=project.id,
        category=NotificationCategory.REPORT,
    )

    db.commit()
    db.refresh(report)
    return report


@router.get("/reports/{report_id}/download")
def download_report_attachment(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="گزارش یافت نشد")
    project = get_project_or_404(db, report.project_id)
    ensure_project_member(project, current_user)

    return build_download_response(
        report.attachment_stored_filename, report.attachment_original_filename
    )
