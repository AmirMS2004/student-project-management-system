"""Builds a downloadable PDF dossier for a project (title, abstract, reports,
grades, defense date) suitable for a defense session or archival.

Persian text needs shaping + bidi reordering before reportlab can lay it out
correctly, and reportlab has no built-in Persian-capable font, so we borrow a
Windows system font (Tahoma ships with every Windows install and covers the
Persian alphabet) instead of bundling a font file with the repo.
"""

import os
from datetime import datetime
from io import BytesIO

import arabic_reshaper
import jdatetime
from bidi.algorithm import get_display
from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

_FONT_NAME = "PersianFont"
_FONT_CANDIDATES = [
    r"C:\Windows\Fonts\tahoma.ttf",
    r"C:\Windows\Fonts\arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]
_font_registered = False


class PersianFontNotFoundError(RuntimeError):
    pass


def _ensure_font_registered():
    global _font_registered
    if _font_registered:
        return
    for path in _FONT_CANDIDATES:
        if os.path.exists(path):
            pdfmetrics.registerFont(TTFont(_FONT_NAME, path))
            _font_registered = True
            return
    raise PersianFontNotFoundError(
        "فونت فارسی برای تولید PDF پیدا نشد (Tahoma یا Arial روی سیستم موجود نیست)"
    )


def _rtl(text) -> str:
    """Reshapes + bidi-reorders Persian/Arabic text for correct PDF rendering."""
    if text is None:
        return "-"
    text = str(text)
    reshaped = arabic_reshaper.reshape(text)
    return get_display(reshaped)


_PERSIAN_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


def _fmt_dt(value: datetime | None, with_time: bool = True) -> str:
    """Formats a datetime as a Jalali (Persian solar) date with Persian
    digits, matching how every date is displayed in the frontend."""
    if not value:
        return "-"
    jalali = jdatetime.datetime.fromgregorian(datetime=value)
    fmt = "%Y/%m/%d %H:%M" if with_time else "%Y/%m/%d"
    return jalali.strftime(fmt).translate(_PERSIAN_DIGITS)


def build_project_pdf(project) -> BytesIO:
    _ensure_font_registered()

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
    )

    body = ParagraphStyle(
        "body", fontName=_FONT_NAME, fontSize=11, alignment=TA_RIGHT, leading=16
    )
    heading = ParagraphStyle(
        "heading",
        fontName=_FONT_NAME,
        fontSize=15,
        leading=20,
        alignment=TA_RIGHT,
        spaceBefore=14,
        spaceAfter=8,
        textColor=colors.HexColor("#1f2937"),
    )
    title_style = ParagraphStyle(
        "title",
        fontName=_FONT_NAME,
        fontSize=19,
        leading=25,
        alignment=TA_RIGHT,
        spaceAfter=6,
    )
    muted = ParagraphStyle(
        "muted", fontName=_FONT_NAME, fontSize=10, alignment=TA_RIGHT, textColor=colors.grey
    )

    elements = []

    elements.append(Paragraph(_rtl("پرونده پروژه"), muted))
    elements.append(Paragraph(_rtl(project.title), title_style))
    elements.append(
        Paragraph(_rtl(f"تولید شده در {_fmt_dt(datetime.utcnow())}"), muted)
    )
    elements.append(Spacer(1, 12))

    info_rows = [
        [_rtl("استاد راهنما"), _rtl(project.professor.full_name if project.professor else "-")],
        [_rtl("دانشجو"), _rtl(project.student.full_name if project.student else "هنوز انتخاب نشده")],
        [_rtl("وضعیت پروژه"), _rtl(_status_label(project.status))],
        [_rtl("درصد پیشرفت"), _rtl(f"{project.progress_percent}%")],
        [_rtl("تاریخ شروع"), _rtl(_fmt_dt(project.start_date, with_time=False))],
        [_rtl("تاریخ پایان"), _rtl(_fmt_dt(project.end_date, with_time=False))],
        [_rtl("تاریخ جلسه دفاع"), _rtl(_fmt_dt(project.defense_date))],
        [_rtl("نتیجه دفاع"), _rtl(_defense_outcome_label(project.defense_outcome))],
        [_rtl("نمره نهایی"), _rtl(project.average_grade if project.average_grade is not None else "ثبت نشده")],
    ]
    info_table = Table(info_rows, colWidths=[5 * cm, 10.5 * cm], hAlign="RIGHT")
    info_table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), _FONT_NAME),
                ("FONTSIZE", (0, 0), (-1, -1), 10.5),
                ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f3f4f6")),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    elements.append(info_table)

    if project.defense_outcome_notes:
        elements.append(
            Paragraph(_rtl(f"توضیحات نتیجه دفاع: {project.defense_outcome_notes}"), muted)
        )

    elements.append(Paragraph(_rtl("چکیده پروژه"), heading))
    elements.append(Paragraph(_rtl(project.abstract or "-"), body))

    elements.append(Paragraph(_rtl("گزارش‌های هفتگی"), heading))
    reports = sorted(project.reports, key=lambda r: r.created_at)
    if not reports:
        elements.append(Paragraph(_rtl("گزارشی ثبت نشده است"), muted))
    else:
        for report in reports:
            elements.append(
                Paragraph(
                    _rtl(f"{_fmt_dt(report.created_at)} — {report.student.full_name if report.student else '-'}"),
                    ParagraphStyle(
                        "reportMeta",
                        fontName=_FONT_NAME,
                        fontSize=10,
                        leading=14,
                        alignment=TA_RIGHT,
                        textColor=colors.HexColor("#374151"),
                        spaceBefore=8,
                    ),
                )
            )
            elements.append(Paragraph(_rtl(report.content), body))
            if report.professor_comment:
                elements.append(
                    Paragraph(_rtl(f"نظر استاد: {report.professor_comment}"), muted)
                )

    elements.append(Paragraph(_rtl("نمرات"), heading))
    if not project.grades:
        elements.append(Paragraph(_rtl("نمره‌ای ثبت نشده است"), muted))
    else:
        grade_rows = [[_rtl("مرحله"), _rtl("نمره"), _rtl("توضیحات"), _rtl("تاریخ")]]
        for grade in sorted(project.grades, key=lambda g: g.graded_at):
            grade_rows.append(
                [
                    _rtl(grade.stage),
                    _rtl(grade.score),
                    _rtl(grade.comment or "-"),
                    _rtl(_fmt_dt(grade.graded_at, with_time=False)),
                ]
            )
        grade_table = Table(
            grade_rows, colWidths=[3.5 * cm, 2 * cm, 6.5 * cm, 3.5 * cm], hAlign="RIGHT"
        )
        grade_table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, -1), _FONT_NAME),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e5e7eb")),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        elements.append(grade_table)
        if project.average_grade is not None:
            elements.append(
                Paragraph(
                    _rtl(f"میانگین نهایی: {project.average_grade} (از {project.grade_count} مرحله)"),
                    ParagraphStyle(
                        "avg",
                        fontName=_FONT_NAME,
                        fontSize=12,
                        leading=16,
                        alignment=TA_RIGHT,
                        spaceBefore=10,
                        textColor=colors.HexColor("#065f46"),
                    ),
                )
            )

    doc.build(elements)
    buffer.seek(0)
    return buffer


def _status_label(status) -> str:
    labels = {
        "open": "باز",
        "pending": "در انتظار تایید",
        "in_progress": "در حال انجام",
        "completed": "خاتمه‌یافته",
        "rejected": "رد شده",
    }
    value = status.value if hasattr(status, "value") else str(status)
    return labels.get(value, value)


def _defense_outcome_label(outcome) -> str:
    if outcome is None:
        return "ثبت نشده"
    labels = {
        "pass": "قبول",
        "needs_revision": "نیاز به اصلاح",
        "fail": "رد",
    }
    value = outcome.value if hasattr(outcome, "value") else str(outcome)
    return labels.get(value, value)
