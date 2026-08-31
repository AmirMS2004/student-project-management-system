"""
ساخت حساب مدیر گروه (Admin).

نقش ادمین از طریق فرم ثبت‌نام عمومی قابل ساخت نیست (برخلاف استاد و دانشجو) —
عمداً همینطور طراحی شده تا کسی نتواند برای خودش دسترسی مدیریتی بسازد. برای
ساخت اولین (یا هر) حساب ادمین، این اسکریپت را از داخل پوشه‌ی backend با
venv فعال اجرا کنید:

    python create_admin.py --name "نام مدیر" --email admin@example.com --phone 09120000000

اگر --password ندهید، به‌صورت تعاملی از شما پرسیده می‌شود.
"""

import argparse
import getpass
import re
import sys

from app.auth import hash_password
from app.database import SessionLocal
from app.models import User, UserRole

PHONE_PATTERN = re.compile(r"^09\d{9}$")


def main():
    parser = argparse.ArgumentParser(description="ساخت حساب مدیر گروه")
    parser.add_argument("--name", required=True, help="نام و نام خانوادگی")
    parser.add_argument("--email", required=True, help="ایمیل")
    parser.add_argument("--phone", required=True, help="شماره موبایل (09xxxxxxxxx)")
    parser.add_argument("--password", help="رمز عبور (اگر ندهید، تعاملی پرسیده می‌شود)")
    args = parser.parse_args()

    if not PHONE_PATTERN.match(args.phone):
        print("خطا: شماره موبایل باید به فرم 09xxxxxxxxx باشد.")
        sys.exit(1)

    password = args.password
    if not password:
        password = getpass.getpass("رمز عبور: ")
        confirm = getpass.getpass("تکرار رمز عبور: ")
        if password != confirm:
            print("خطا: رمز عبور و تکرار آن یکسان نیستند.")
            sys.exit(1)

    if len(password) < 6:
        print("خطا: رمز عبور باید حداقل ۶ کاراکتر باشد.")
        sys.exit(1)

    db = SessionLocal()
    try:
        existing = (
            db.query(User)
            .filter((User.email == args.email) | (User.phone_number == args.phone))
            .first()
        )
        if existing:
            print(f"خطا: کاربری با این ایمیل یا شماره موبایل از قبل وجود دارد (id={existing.id}).")
            sys.exit(1)

        admin = User(
            full_name=args.name,
            email=args.email,
            phone_number=args.phone,
            hashed_password=hash_password(password),
            role=UserRole.ADMIN,
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        print(f"حساب مدیر گروه با موفقیت ساخته شد (id={admin.id}, email={admin.email}).")
    finally:
        db.close()


if __name__ == "__main__":
    main()
