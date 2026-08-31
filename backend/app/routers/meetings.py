from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from .. import schemas
from ..access import ensure_project_member, ensure_project_owner, get_project_or_404
from ..auth import get_current_user, require_professor, require_student
from ..database import get_db
from ..models import Meeting, MeetingRequest, NotificationCategory, RequestStatus, User
from ..utils import notify

router = APIRouter(prefix="/api", tags=["meetings"])


@router.post(
    "/projects/{project_id}/meetings",
    response_model=schemas.MeetingOut,
    status_code=status.HTTP_201_CREATED,
)
def create_meeting(
    project_id: int,
    payload: schemas.MeetingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_professor),
):
    project = get_project_or_404(db, project_id)
    ensure_project_member(project, current_user)

    meeting = Meeting(
        project_id=project.id,
        scheduled_at=payload.scheduled_at,
        location=payload.location,
    )
    db.add(meeting)

    if project.student_id:
        notify(
            db,
            project.student_id,
            f'جلسه جدیدی برای پروژه "{project.title}" تعیین شد',
            link=f"/projects/{project.id}",
            project_id=project.id,
            category=NotificationCategory.MEETING,
        )

    db.commit()
    db.refresh(meeting)
    return meeting


@router.post(
    "/projects/{project_id}/meeting-requests",
    response_model=schemas.MeetingRequestOut,
    status_code=status.HTTP_201_CREATED,
)
def propose_meeting(
    project_id: int,
    payload: schemas.MeetingRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student),
):
    project = get_project_or_404(db, project_id)
    if project.student_id != current_user.id:
        raise HTTPException(status_code=403, detail="دسترسی غیرمجاز")

    meeting_request = MeetingRequest(
        project_id=project.id,
        student_id=current_user.id,
        scheduled_at=payload.scheduled_at,
        location=payload.location,
        message=payload.message,
    )
    db.add(meeting_request)

    notify(
        db,
        project.professor_id,
        f'دانشجو زمان جلسه‌ای برای پروژه "{project.title}" پیشنهاد داد',
        link=f"/projects/{project.id}",
        project_id=project.id,
        category=NotificationCategory.MEETING,
    )

    db.commit()
    db.refresh(meeting_request)
    return meeting_request


@router.get(
    "/projects/{project_id}/meeting-requests",
    response_model=list[schemas.MeetingRequestOut],
)
def list_meeting_requests(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = get_project_or_404(db, project_id)
    ensure_project_member(project, current_user)

    return (
        db.query(MeetingRequest)
        .options(joinedload(MeetingRequest.student))
        .filter(MeetingRequest.project_id == project_id)
        .order_by(MeetingRequest.requested_at.desc())
        .all()
    )


@router.patch(
    "/meeting-requests/{request_id}", response_model=schemas.MeetingRequestOut
)
def decide_meeting_request(
    request_id: int,
    payload: schemas.MeetingRequestDecision,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_professor),
):
    meeting_request = (
        db.query(MeetingRequest).filter(MeetingRequest.id == request_id).first()
    )
    if not meeting_request:
        raise HTTPException(status_code=404, detail="درخواست جلسه یافت نشد")

    project = get_project_or_404(db, meeting_request.project_id)
    ensure_project_owner(project, current_user)
    if meeting_request.status != RequestStatus.PENDING:
        raise HTTPException(status_code=400, detail="این درخواست قبلا بررسی شده است")

    meeting_request.decided_at = datetime.utcnow()

    if payload.approve:
        meeting_request.status = RequestStatus.APPROVED
        db.add(
            Meeting(
                project_id=project.id,
                scheduled_at=meeting_request.scheduled_at,
                location=meeting_request.location,
            )
        )
        notify(
            db,
            meeting_request.student_id,
            f'زمان جلسه‌ی پیشنهادی شما برای پروژه "{project.title}" تایید شد',
            link=f"/projects/{project.id}",
            project_id=project.id,
            category=NotificationCategory.MEETING,
        )
    else:
        meeting_request.status = RequestStatus.REJECTED
        notify(
            db,
            meeting_request.student_id,
            f'زمان جلسه‌ی پیشنهادی شما برای پروژه "{project.title}" رد شد',
            link=f"/projects/{project.id}",
            project_id=project.id,
            category=NotificationCategory.MEETING,
        )

    db.commit()
    db.refresh(meeting_request)
    return meeting_request


@router.get("/projects/{project_id}/meetings", response_model=list[schemas.MeetingOut])
def list_meetings(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = get_project_or_404(db, project_id)
    ensure_project_member(project, current_user)

    return (
        db.query(Meeting)
        .filter(Meeting.project_id == project.id)
        .order_by(Meeting.scheduled_at.desc())
        .all()
    )


@router.patch("/meetings/{meeting_id}", response_model=schemas.MeetingOut)
def update_meeting(
    meeting_id: int,
    payload: schemas.MeetingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_professor),
):
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="جلسه یافت نشد")
    project = get_project_or_404(db, meeting.project_id)
    ensure_project_owner(project, current_user)

    data = payload.model_dump(exclude_unset=True)
    report_added = "report" in data and data["report"]
    for key, value in data.items():
        setattr(meeting, key, value)

    if report_added and project.student_id:
        notify(
            db,
            project.student_id,
            f'گزارش جلسه پروژه "{project.title}" ثبت شد',
            link=f"/projects/{project.id}",
            project_id=project.id,
            category=NotificationCategory.MEETING,
        )

    db.commit()
    db.refresh(meeting)
    return meeting
