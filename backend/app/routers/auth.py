import secrets

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import schemas
from ..auth import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from ..captcha import generate_captcha, verify_captcha
from ..database import get_db
from ..models import User, UserRole
from ..settings import get_professor_invite_code

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.get("/captcha", response_model=schemas.CaptchaOut)
def get_captcha():
    captcha_id, image_base64 = generate_captcha()
    return schemas.CaptchaOut(captcha_id=captcha_id, image_base64=image_base64)


@router.post("/register", response_model=schemas.Token, status_code=status.HTTP_201_CREATED)
def register(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    if not verify_captcha(payload.captcha_id, payload.captcha_answer):
        raise HTTPException(status_code=400, detail="کد امنیتی وارد شده صحیح نیست")

    if payload.role == UserRole.ADMIN:
        raise HTTPException(
            status_code=400,
            detail="حساب مدیر گروه فقط توسط مدیر سامانه و از طریق اسکریپت مخصوص ساخته می‌شود",
        )

    if payload.role == UserRole.PROFESSOR:
        current_invite_code = get_professor_invite_code(db)
        if not payload.invite_code or not secrets.compare_digest(
            payload.invite_code, current_invite_code
        ):
            raise HTTPException(status_code=400, detail="کد دعوت استاد نامعتبر است")

    existing_email = db.query(User).filter(User.email == payload.email).first()
    if existing_email:
        raise HTTPException(status_code=400, detail="این ایمیل قبلا ثبت شده است")

    existing_phone = (
        db.query(User).filter(User.phone_number == payload.phone_number).first()
    )
    if existing_phone:
        raise HTTPException(status_code=400, detail="این شماره موبایل قبلا ثبت شده است")

    user = User(
        full_name=payload.full_name,
        email=payload.email,
        phone_number=payload.phone_number,
        hashed_password=hash_password(payload.password),
        role=payload.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": str(user.id)})
    return schemas.Token(access_token=token, user=user)


@router.post("/login", response_model=schemas.Token)
def login(payload: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="ایمیل یا رمز عبور اشتباه است")

    token = create_access_token({"sub": str(user.id)})
    return schemas.Token(access_token=token, user=user)


@router.get("/me", response_model=schemas.UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/me", response_model=schemas.UserOut)
def update_me(
    payload: schemas.ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    data = payload.model_dump(exclude_unset=True)

    if "email" in data and data["email"] != current_user.email:
        existing = (
            db.query(User)
            .filter(User.email == data["email"], User.id != current_user.id)
            .first()
        )
        if existing:
            raise HTTPException(status_code=400, detail="این ایمیل قبلا ثبت شده است")

    if "phone_number" in data and data["phone_number"] != current_user.phone_number:
        existing = (
            db.query(User)
            .filter(
                User.phone_number == data["phone_number"], User.id != current_user.id
            )
            .first()
        )
        if existing:
            raise HTTPException(status_code=400, detail="این شماره موبایل قبلا ثبت شده است")

    for key, value in data.items():
        setattr(current_user, key, value)

    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/me/password")
def change_password(
    payload: schemas.PasswordChange,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="رمز عبور فعلی اشتباه است")

    current_user.hashed_password = hash_password(payload.new_password)
    db.commit()
    return {"status": "ok"}
