from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from .models import (
    DefenseOutcome,
    FileCategory,
    NotificationCategory,
    ProjectStatus,
    RequestStatus,
    UserRole,
)


# ---------- Auth / Users ----------


class UserCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    phone_number: str = Field(pattern=r"^09\d{9}$")
    password: str = Field(min_length=6, max_length=128)
    role: UserRole
    captcha_id: str
    captcha_answer: str
    invite_code: Optional[str] = None


class UserOut(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    phone_number: str
    role: UserRole
    created_at: datetime

    class Config:
        from_attributes = True


class CaptchaOut(BaseModel):
    captcha_id: str
    image_base64: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ProfileUpdate(BaseModel):
    full_name: Optional[str] = Field(default=None, min_length=2, max_length=150)
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = Field(default=None, pattern=r"^09\d{9}$")


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(min_length=6, max_length=128)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ---------- Projects ----------


class ProjectCreate(BaseModel):
    title: str = Field(min_length=3, max_length=255)
    abstract: Optional[str] = None


class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    abstract: Optional[str] = None
    status: Optional[ProjectStatus] = None
    progress_percent: Optional[int] = Field(default=None, ge=0, le=100)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    defense_date: Optional[datetime] = None
    defense_outcome: Optional[DefenseOutcome] = None
    defense_outcome_notes: Optional[str] = None
    # Weekly report deadline: e.g. report_weekday=6 (Sunday) + "23:59" means
    # "every Sunday at 23:59". Both must be cleared together (set to None) to
    # remove the deadline.
    report_weekday: Optional[int] = Field(default=None, ge=0, le=6)
    report_deadline_time: Optional[str] = Field(default=None, pattern=r"^\d{2}:\d{2}$")


class ProjectOut(BaseModel):
    id: int
    title: str
    abstract: Optional[str]
    status: ProjectStatus
    progress_percent: int
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    defense_date: Optional[datetime]
    defense_outcome: Optional[DefenseOutcome] = None
    defense_outcome_notes: Optional[str] = None
    created_at: datetime
    professor_id: int
    student_id: Optional[int]
    professor: Optional[UserOut] = None
    student: Optional[UserOut] = None
    brief_original_filename: Optional[str] = None
    average_grade: Optional[float] = None
    grade_count: int = 0
    report_weekday: Optional[int] = None
    report_deadline_time: Optional[str] = None

    class Config:
        from_attributes = True


# ---------- Project Requests ----------


class ProjectRequestCreate(BaseModel):
    message: Optional[str] = None


class ProjectRequestOut(BaseModel):
    id: int
    project_id: int
    student_id: int
    status: RequestStatus
    message: Optional[str]
    requested_at: datetime
    decided_at: Optional[datetime]
    student: Optional[UserOut] = None
    project: Optional[ProjectOut] = None

    class Config:
        from_attributes = True


class ProjectRequestDecision(BaseModel):
    approve: bool


# ---------- Meetings ----------


class MeetingCreate(BaseModel):
    scheduled_at: datetime
    location: Optional[str] = None


class MeetingUpdate(BaseModel):
    scheduled_at: Optional[datetime] = None
    location: Optional[str] = None
    report: Optional[str] = None


class MeetingOut(BaseModel):
    id: int
    project_id: int
    scheduled_at: datetime
    location: Optional[str]
    report: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- Meeting Requests (student-proposed meeting times) ----------


class MeetingRequestCreate(BaseModel):
    scheduled_at: datetime
    location: Optional[str] = None
    message: Optional[str] = None


class MeetingRequestOut(BaseModel):
    id: int
    project_id: int
    student_id: int
    scheduled_at: datetime
    location: Optional[str]
    message: Optional[str]
    status: RequestStatus
    requested_at: datetime
    decided_at: Optional[datetime]
    student: Optional[UserOut] = None

    class Config:
        from_attributes = True


class MeetingRequestDecision(BaseModel):
    approve: bool


# ---------- Reports ----------


class ReportComment(BaseModel):
    professor_comment: str = Field(min_length=1)


class ReportOut(BaseModel):
    id: int
    project_id: int
    student_id: int
    content: str
    attachment_original_filename: Optional[str] = None
    professor_comment: Optional[str]
    created_at: datetime
    commented_at: Optional[datetime]

    class Config:
        from_attributes = True


# ---------- Grades ----------


class GradeCreate(BaseModel):
    stage: str = Field(min_length=1, max_length=100)
    score: int = Field(ge=0, le=100)
    comment: Optional[str] = None


class GradeOut(BaseModel):
    id: int
    project_id: int
    stage: str
    score: int
    comment: Optional[str]
    graded_at: datetime

    class Config:
        from_attributes = True


# ---------- Files ----------


class ProjectFileOut(BaseModel):
    id: int
    project_id: int
    uploaded_by_id: int
    category: FileCategory
    original_filename: str
    description: Optional[str]
    uploaded_at: datetime

    class Config:
        from_attributes = True


# ---------- Messages ----------


class MessageOut(BaseModel):
    id: int
    project_id: int
    sender_id: int
    recipient_id: int
    content: Optional[str]
    attachment_original_filename: Optional[str] = None
    sent_at: datetime
    read_at: Optional[datetime]
    sender: Optional[UserOut] = None

    class Config:
        from_attributes = True


# ---------- Notifications ----------


class NotificationOut(BaseModel):
    id: int
    content: str
    link: Optional[str]
    project_id: Optional[int] = None
    category: Optional[NotificationCategory] = None
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- Dashboard ----------


class DashboardStats(BaseModel):
    total_projects: int
    active_projects: int
    completed_projects: int
    average_duration_days: Optional[float]
    average_progress_percent: float


# ---------- Admin ----------


class AdminStats(BaseModel):
    total_projects: int
    open_projects: int
    active_projects: int
    completed_projects: int
    average_duration_days: Optional[float]
    average_progress_percent: float
    total_professors: int
    total_students: int


# ---------- Calendar ----------


class CalendarEventOut(BaseModel):
    event_type: str  # "meeting" | "defense" | "report_deadline"
    title: str
    occurs_at: datetime
    project_id: int
    project_title: str
    extra: Optional[str] = None


# ---------- Admin settings ----------


class AdminSettingsOut(BaseModel):
    professor_invite_code: str


class AdminSettingsUpdate(BaseModel):
    professor_invite_code: str = Field(min_length=4, max_length=100)
