from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session, joinedload

from .. import schemas
from ..access import ensure_project_member, get_project_or_404
from ..auth import get_current_user
from ..database import get_db
from ..file_storage import build_download_response, save_upload
from ..models import Message, NotificationCategory, User
from ..utils import notify

router = APIRouter(prefix="/api", tags=["messages"])


@router.post(
    "/projects/{project_id}/messages",
    response_model=schemas.MessageOut,
    status_code=status.HTTP_201_CREATED,
)
async def send_message(
    project_id: int,
    recipient_id: int = Form(...),
    content: str = Form(""),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = get_project_or_404(db, project_id)
    ensure_project_member(project, current_user)

    valid_recipients = {project.professor_id, project.student_id}
    if recipient_id not in valid_recipients or recipient_id == current_user.id:
        raise HTTPException(status_code=400, detail="گیرنده پیام نامعتبر است")

    content = (content or "").strip()
    if not content and not file:
        raise HTTPException(status_code=400, detail="متن پیام یا فایل الزامی است")

    message = Message(
        project_id=project.id,
        sender_id=current_user.id,
        recipient_id=recipient_id,
        content=content or None,
    )

    if file:
        original_name, stored_name = await save_upload(file)
        message.attachment_original_filename = original_name
        message.attachment_stored_filename = stored_name

    db.add(message)

    notify(
        db,
        recipient_id,
        f'پیام جدید در پروژه "{project.title}" از {current_user.full_name}',
        link=f"/projects/{project.id}",
        project_id=project.id,
        category=NotificationCategory.MESSAGE,
    )

    db.commit()
    db.refresh(message)
    return message


@router.get("/projects/{project_id}/messages", response_model=list[schemas.MessageOut])
def list_messages(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = get_project_or_404(db, project_id)
    ensure_project_member(project, current_user)

    messages = (
        db.query(Message)
        .options(joinedload(Message.sender))
        .filter(Message.project_id == project_id)
        .order_by(Message.sent_at.asc())
        .all()
    )

    unread = [
        m for m in messages if m.recipient_id == current_user.id and m.read_at is None
    ]
    for m in unread:
        m.read_at = datetime.utcnow()
    if unread:
        db.commit()

    return messages


@router.get("/messages/{message_id}/download")
def download_message_attachment(
    message_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="پیام یافت نشد")
    if current_user.id not in (message.sender_id, message.recipient_id):
        raise HTTPException(status_code=403, detail="دسترسی غیرمجاز")

    return build_download_response(
        message.attachment_stored_filename, message.attachment_original_filename
    )
