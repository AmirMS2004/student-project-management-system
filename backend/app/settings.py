"""Runtime-editable system settings, backed by the app_settings key/value
table. Currently just the professor sign-up invite code — moved out of a
static environment variable so an admin can rotate it from the UI without
restarting the server.
"""

from sqlalchemy.orm import Session

from .config import PROFESSOR_INVITE_CODE
from .models import AppSetting

PROFESSOR_INVITE_CODE_KEY = "professor_invite_code"


def get_setting(db: Session, key: str, default: str) -> str:
    row = db.query(AppSetting).filter(AppSetting.key == key).first()
    return row.value if row else default


def set_setting(db: Session, key: str, value: str) -> None:
    row = db.query(AppSetting).filter(AppSetting.key == key).first()
    if row:
        row.value = value
    else:
        db.add(AppSetting(key=key, value=value))


def get_professor_invite_code(db: Session) -> str:
    return get_setting(db, PROFESSOR_INVITE_CODE_KEY, PROFESSOR_INVITE_CODE)


def set_professor_invite_code(db: Session, value: str) -> None:
    set_setting(db, PROFESSOR_INVITE_CODE_KEY, value)
