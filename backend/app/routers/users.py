from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import schemas
from ..auth import get_current_user
from ..database import get_db
from ..models import User, UserRole

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/professors", response_model=list[schemas.UserOut])
def list_professors(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(User)
        .filter(User.role == UserRole.PROFESSOR)
        .order_by(User.full_name)
        .all()
    )
