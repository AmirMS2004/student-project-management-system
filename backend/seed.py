"""
داده‌های نمونه برای توسعه‌ی لوکال.

اجرا (از داخل پوشه‌ی backend، با venv فعال):
    python seed.py

این اسکریپت idempotent است: اگر کاربری با همان ایمیل از قبل وجود داشته باشد،
دوباره ساخته نمی‌شود، پس اجرای چندباره‌اش بی‌خطر است.
"""

from datetime import datetime, timedelta

from app.auth import hash_password
from app.database import SessionLocal
from app.models import (
    Grade,
    Meeting,
    Message,
    NotificationCategory,
    Project,
    ProjectRequest,
    ProjectStatus,
    RequestStatus,
    Report,
    User,
    UserRole,
)
from app.utils import notify

DEFAULT_PASSWORD = "password123"


def get_or_create_user(db, *, full_name, email, phone_number, role):
    user = db.query(User).filter(User.email == email).first()
    if user:
        return user, False
    user = User(
        full_name=full_name,
        email=email,
        phone_number=phone_number,
        hashed_password=hash_password(DEFAULT_PASSWORD),
        role=role,
    )
    db.add(user)
    db.flush()
    return user, True


def get_or_create_project(db, *, title, **kwargs):
    project = db.query(Project).filter(Project.title == title).first()
    if project:
        return project, False
    project = Project(title=title, **kwargs)
    db.add(project)
    db.flush()
    return project, True


def main():
    db = SessionLocal()
    created_users = []

    try:
        admin, is_new = get_or_create_user(
            db,
            full_name="مدیر گروه",
            email="admin@example.com",
            phone_number="09190000000",
            role=UserRole.ADMIN,
        )
        if is_new:
            created_users.append(admin)

        professor1, is_new = get_or_create_user(
            db,
            full_name="دکتر احمدی",
            email="professor1@example.com",
            phone_number="09120000001",
            role=UserRole.PROFESSOR,
        )
        if is_new:
            created_users.append(professor1)

        professor2, is_new = get_or_create_user(
            db,
            full_name="دکتر رضایی",
            email="professor2@example.com",
            phone_number="09120000002",
            role=UserRole.PROFESSOR,
        )
        if is_new:
            created_users.append(professor2)

        students = []
        student_names = [
            ("علی محمدی", "student1@example.com", "09130000001"),
            ("مریم کریمی", "student2@example.com", "09130000002"),
            ("رضا صادقی", "student3@example.com", "09130000003"),
            ("سارا حسینی", "student4@example.com", "09130000004"),
        ]
        for full_name, email, phone in student_names:
            student, is_new = get_or_create_user(
                db,
                full_name=full_name,
                email=email,
                phone_number=phone,
                role=UserRole.STUDENT,
            )
            students.append(student)
            if is_new:
                created_users.append(student)

        db.flush()
        student1, student2, student3, student4 = students

        # --- Project 1: open, no student yet ---
        project_open, _ = get_or_create_project(
            db,
            title="تشخیص چهره با شبکه‌های عصبی کانولوشنی",
            abstract="پیاده‌سازی و مقایسه‌ی چند معماری CNN برای تشخیص چهره روی دیتاست‌های استاندارد.",
            professor_id=professor1.id,
            status=ProjectStatus.OPEN,
        )

        # --- Project 2: open, no student yet (different professor) ---
        project_open2, _ = get_or_create_project(
            db,
            title="سامانه توصیه‌گر فیلم مبتنی بر یادگیری ماشین",
            abstract="طراحی یک موتور پیشنهاددهنده با فیلترینگ مشارکتی و محتوامحور.",
            professor_id=professor2.id,
            status=ProjectStatus.OPEN,
        )

        # --- Project 3: in progress, with meetings/reports/grades ---
        project_active, is_new_active = get_or_create_project(
            db,
            title="بهینه‌سازی الگوریتم مسیریابی ربات با A* بهبودیافته",
            abstract="پیاده‌سازی و ارزیابی یک نسخه‌ی بهبودیافته از الگوریتم A* برای مسیریابی در محیط‌های پویا.",
            professor_id=professor1.id,
            student_id=student1.id,
            status=ProjectStatus.IN_PROGRESS,
            progress_percent=45,
            start_date=datetime.utcnow() - timedelta(days=30),
        )
        if is_new_active:
            db.add(
                Meeting(
                    project_id=project_active.id,
                    scheduled_at=datetime.utcnow() - timedelta(days=7),
                    location="دفتر استاد - اتاق ۳۰۲",
                    report="پیشرفت کلی پروژه بررسی شد. دانشجو پیاده‌سازی اولیه‌ی الگوریتم را ارائه داد.",
                )
            )
            db.add(
                Meeting(
                    project_id=project_active.id,
                    scheduled_at=datetime.utcnow() + timedelta(days=3),
                    location="آنلاین - گوگل میت",
                )
            )
            db.add(
                Report(
                    project_id=project_active.id,
                    student_id=student1.id,
                    content="این هفته پیاده‌سازی اولیه‌ی الگوریتم A* را کامل کردم و شروع به تست روی نقشه‌های نمونه کردم.",
                    professor_comment="عالی بود، لطفا نتایج تست را هم مستند کن.",
                    commented_at=datetime.utcnow() - timedelta(days=2),
                )
            )
            db.add(
                Report(
                    project_id=project_active.id,
                    student_id=student1.id,
                    content="تست‌های اولیه روی سه نقشه‌ی مختلف انجام شد. نتایج در حال مستندسازی است.",
                )
            )
            db.add(
                Grade(
                    project_id=project_active.id,
                    stage="پروپوزال",
                    score=90,
                    comment="تعریف مساله و مرور ادبیات قوی بود.",
                )
            )
            db.add(
                Message(
                    project_id=project_active.id,
                    sender_id=student1.id,
                    recipient_id=professor1.id,
                    content="استاد، برای جلسه‌ی هفته‌ی آینده چه موضوعی رو آماده کنم؟",
                )
            )
            db.add(
                Message(
                    project_id=project_active.id,
                    sender_id=professor1.id,
                    recipient_id=student1.id,
                    content="نتایج تست‌های اخیر رو آماده کن تا با هم مرورشون کنیم.",
                )
            )
            notify(
                db,
                professor1.id,
                f'گزارش هفتگی جدید برای پروژه "{project_active.title}" ثبت شد',
                link=f"/projects/{project_active.id}",
                project_id=project_active.id,
                category=NotificationCategory.REPORT,
            )

        # --- Project 4: completed ---
        project_done, is_new_done = get_or_create_project(
            db,
            title="طراحی سامانه مدیریت انبار هوشمند",
            abstract="طراحی و پیاده‌سازی یک سامانه‌ی مدیریت موجودی انبار با قابلیت پیش‌بینی تقاضا.",
            professor_id=professor2.id,
            student_id=student3.id,
            status=ProjectStatus.COMPLETED,
            progress_percent=100,
            start_date=datetime.utcnow() - timedelta(days=180),
            end_date=datetime.utcnow() - timedelta(days=10),
        )
        if is_new_done:
            db.add(
                Grade(
                    project_id=project_done.id,
                    stage="دفاع نهایی",
                    score=95,
                    comment="دفاع بسیار خوبی داشت، پروژه با موفقیت به پایان رسید.",
                )
            )

        db.flush()

        # --- Pending request from student2 on the first open project ---
        existing_request = (
            db.query(ProjectRequest)
            .filter(
                ProjectRequest.project_id == project_open.id,
                ProjectRequest.student_id == student2.id,
            )
            .first()
        )
        if not existing_request:
            db.add(
                ProjectRequest(
                    project_id=project_open.id,
                    student_id=student2.id,
                    status=RequestStatus.PENDING,
                    message="به حوزه‌ی بینایی ماشین علاقه‌مندم و پیش‌زمینه‌ی مناسبی در پایتون دارم.",
                )
            )
            notify(
                db,
                professor1.id,
                f'دانشجوی جدیدی برای پروژه "{project_open.title}" درخواست داد',
                link=f"/projects/{project_open.id}",
                project_id=project_open.id,
                category=NotificationCategory.REQUEST,
            )

        # a second, older pending request from student4 on the same project
        existing_request2 = (
            db.query(ProjectRequest)
            .filter(
                ProjectRequest.project_id == project_open.id,
                ProjectRequest.student_id == student4.id,
            )
            .first()
        )
        if not existing_request2:
            db.add(
                ProjectRequest(
                    project_id=project_open.id,
                    student_id=student4.id,
                    status=RequestStatus.PENDING,
                    message="سابقه‌ی کار با OpenCV دارم.",
                )
            )

        db.commit()

        print("Seed کامل شد.\n")
        if created_users:
            print("کاربران جدید ساخته‌شده (رمز عبور همه: password123):")
            for u in created_users:
                role_label = {
                    UserRole.ADMIN: "مدیر گروه",
                    UserRole.PROFESSOR: "استاد",
                    UserRole.STUDENT: "دانشجو",
                }[u.role]
                print(f"  - {u.email}  ({role_label} - {u.full_name})")
        else:
            print("کاربری اضافه نشد (احتمالا قبلا seed شده بود).")

        print("\nپروژه‌های نمونه:")
        for p in [project_open, project_open2, project_active, project_done]:
            print(f"  - [{p.status.value}] {p.title}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
