"""Shared project-access helpers used across routers to avoid repeating the
same "fetch project or 404" / "is this user allowed here" checks everywhere."""

from fastapi import HTTPException
from sqlalchemy.orm import Session

from .models import Project, User, UserRole


def get_project_or_404(db: Session, project_id: int) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="پروژه یافت نشد")
    return project


def is_project_member(project: Project, user: User) -> bool:
    return (user.role == UserRole.PROFESSOR and project.professor_id == user.id) or (
        user.role == UserRole.STUDENT and project.student_id == user.id
    )


def ensure_project_member(project: Project, user: User) -> None:
    if not is_project_member(project, user):
        raise HTTPException(status_code=403, detail="دسترسی غیرمجاز")


def ensure_project_owner(project: Project, user: User) -> None:
    if project.professor_id != user.id:
        raise HTTPException(status_code=403, detail="دسترسی غیرمجاز")
