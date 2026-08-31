import enum
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from .database import Base


class UserRole(str, enum.Enum):
    PROFESSOR = "professor"
    STUDENT = "student"
    ADMIN = "admin"


class ProjectStatus(str, enum.Enum):
    OPEN = "open"  # available, no student assigned yet
    PENDING = "pending"  # a request is awaiting professor decision
    IN_PROGRESS = "in_progress"  # student assigned, work ongoing
    COMPLETED = "completed"
    REJECTED = "rejected"  # closed without completion


class RequestStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class DefenseOutcome(str, enum.Enum):
    PASS_ = "pass"
    NEEDS_REVISION = "needs_revision"
    FAIL = "fail"


class FileCategory(str, enum.Enum):
    REQUIRED = "required"  # uploaded by professor as required material
    SUBMISSION = "submission"  # uploaded by student as deliverable


class NotificationCategory(str, enum.Enum):
    PROJECT = "project"
    REQUEST = "request"
    MEETING = "meeting"
    REPORT = "report"
    GRADE = "grade"
    FILE = "file"
    MESSAGE = "message"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(150), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    phone_number = Column(String(20), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    projects_as_professor = relationship(
        "Project", back_populates="professor", foreign_keys="Project.professor_id"
    )
    projects_as_student = relationship(
        "Project", back_populates="student", foreign_keys="Project.student_id"
    )


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    abstract = Column(Text, nullable=True)
    status = Column(Enum(ProjectStatus), default=ProjectStatus.OPEN, nullable=False)
    progress_percent = Column(Integer, default=0)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    defense_date = Column(DateTime, nullable=True)
    defense_outcome = Column(Enum(DefenseOutcome), nullable=True)
    defense_outcome_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Weekly report deadline: a fixed weekday (0=Monday .. 6=Sunday, same as
    # Python's date.weekday()) + time-of-day, set by the professor. Left null
    # means no recurring deadline is configured for this project.
    report_weekday = Column(Integer, nullable=True)
    report_deadline_time = Column(String(5), nullable=True)  # "HH:MM"

    brief_original_filename = Column(String(255), nullable=True)
    brief_stored_filename = Column(String(255), nullable=True)

    professor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    professor = relationship(
        "User", back_populates="projects_as_professor", foreign_keys=[professor_id]
    )
    student = relationship(
        "User", back_populates="projects_as_student", foreign_keys=[student_id]
    )

    requests = relationship(
        "ProjectRequest", back_populates="project", cascade="all, delete-orphan"
    )
    meetings = relationship(
        "Meeting", back_populates="project", cascade="all, delete-orphan"
    )
    meeting_requests = relationship(
        "MeetingRequest", back_populates="project", cascade="all, delete-orphan"
    )
    reports = relationship(
        "Report", back_populates="project", cascade="all, delete-orphan"
    )
    grades = relationship(
        "Grade", back_populates="project", cascade="all, delete-orphan"
    )
    files = relationship(
        "ProjectFile", back_populates="project", cascade="all, delete-orphan"
    )
    messages = relationship(
        "Message", back_populates="project", cascade="all, delete-orphan"
    )

    @property
    def grade_count(self) -> int:
        return len(self.grades)

    @property
    def average_grade(self):
        if not self.grades:
            return None
        return round(sum(g.score for g in self.grades) / len(self.grades), 1)


class ProjectRequest(Base):
    __tablename__ = "project_requests"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(Enum(RequestStatus), default=RequestStatus.PENDING, nullable=False)
    message = Column(Text, nullable=True)
    requested_at = Column(DateTime, default=datetime.utcnow)
    decided_at = Column(DateTime, nullable=True)

    project = relationship("Project", back_populates="requests")
    student = relationship("User")


class Meeting(Base):
    __tablename__ = "meetings"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    scheduled_at = Column(DateTime, nullable=False)
    location = Column(String(255), nullable=True)
    report = Column(Text, nullable=True)  # filled in after the meeting happens
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="meetings")


class MeetingRequest(Base):
    """A meeting time proposed by the student, awaiting the professor's
    approval — mirrors ProjectRequest's pending/approved/rejected flow.
    Approving one creates the actual Meeting row."""

    __tablename__ = "meeting_requests"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    scheduled_at = Column(DateTime, nullable=False)
    location = Column(String(255), nullable=True)
    message = Column(Text, nullable=True)
    status = Column(Enum(RequestStatus), default=RequestStatus.PENDING, nullable=False)
    requested_at = Column(DateTime, default=datetime.utcnow)
    decided_at = Column(DateTime, nullable=True)

    project = relationship("Project", back_populates="meeting_requests")
    student = relationship("User")


class Report(Base):
    """Weekly progress report submitted by the student."""

    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    attachment_original_filename = Column(String(255), nullable=True)
    attachment_stored_filename = Column(String(255), nullable=True)
    professor_comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    commented_at = Column(DateTime, nullable=True)

    project = relationship("Project", back_populates="reports")
    student = relationship("User")


class Grade(Base):
    __tablename__ = "grades"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    stage = Column(String(100), nullable=False)
    score = Column(Integer, nullable=False)
    comment = Column(Text, nullable=True)
    graded_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="grades")


class ProjectFile(Base):
    __tablename__ = "project_files"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    uploaded_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    category = Column(Enum(FileCategory), nullable=False)
    original_filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), nullable=False)
    description = Column(String(500), nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="files")
    uploaded_by = relationship("User")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    recipient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=True)
    attachment_original_filename = Column(String(255), nullable=True)
    attachment_stored_filename = Column(String(255), nullable=True)
    sent_at = Column(DateTime, default=datetime.utcnow)
    read_at = Column(DateTime, nullable=True)

    project = relationship("Project", back_populates="messages")
    sender = relationship("User", foreign_keys=[sender_id])
    recipient = relationship("User", foreign_keys=[recipient_id])


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(String(500), nullable=False)
    link = Column(String(255), nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    category = Column(Enum(NotificationCategory), nullable=True)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")


class ReminderLog(Base):
    """Tracks which calendar-event reminders (meeting, defense date, weekly
    report deadline) have already been sent, so the periodic background job
    never notifies a user twice for the same occurrence."""

    __tablename__ = "reminder_logs"

    id = Column(Integer, primary_key=True, index=True)
    event_key = Column(String(255), unique=True, nullable=False, index=True)
    sent_at = Column(DateTime, default=datetime.utcnow)


class AppSetting(Base):
    """Simple key/value store for system-wide settings an admin can change at
    runtime (currently just the professor sign-up invite code) without
    needing to edit environment variables and restart the server."""

    __tablename__ = "app_settings"

    key = Column(String(100), primary_key=True)
    value = Column(String(255), nullable=False)
