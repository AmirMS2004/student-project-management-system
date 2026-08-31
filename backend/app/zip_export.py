"""Bundles a project's full archive (dossier PDF + every uploaded file) into
a single ZIP, for handing over to a defense committee or the university
archive — the natural next step after the PDF-only export.
"""

from io import BytesIO
from zipfile import ZipFile, ZIP_DEFLATED

from . import file_storage
from .pdf_export import build_project_pdf


def _add_stored_file(zf: ZipFile, folder: str, stored_filename: str, arc_name: str) -> None:
    path = file_storage.UPLOAD_DIR / stored_filename
    if path.exists():
        zf.write(path, arcname=f"{folder}/{arc_name}")


def build_project_zip(project) -> BytesIO:
    buffer = BytesIO()
    with ZipFile(buffer, "w", ZIP_DEFLATED) as zf:
        pdf_bytes = build_project_pdf(project)
        zf.writestr("پرونده-پروژه.pdf", pdf_bytes.read())

        if project.brief_stored_filename:
            _add_stored_file(
                zf,
                "فایل-توضیحات-تکمیلی",
                project.brief_stored_filename,
                project.brief_original_filename or project.brief_stored_filename,
            )

        for report in project.reports:
            if report.attachment_stored_filename:
                _add_stored_file(
                    zf,
                    "گزارش‌ها",
                    report.attachment_stored_filename,
                    f"{report.id}-{report.attachment_original_filename}",
                )

        for project_file in project.files:
            _add_stored_file(
                zf,
                "فایل‌ها",
                project_file.stored_filename,
                f"{project_file.id}-{project_file.original_filename}",
            )

        for message in project.messages:
            if message.attachment_stored_filename:
                _add_stored_file(
                    zf,
                    "پیام‌ها",
                    message.attachment_stored_filename,
                    f"{message.id}-{message.attachment_original_filename}",
                )

    buffer.seek(0)
    return buffer
