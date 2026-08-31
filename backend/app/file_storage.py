"""Shared helpers for storing and serving uploaded files, used by every
router that accepts a file (projects, files, reports, messages)."""

import uuid
from pathlib import Path
from typing import Optional

from fastapi import HTTPException, UploadFile
from fastapi.responses import FileResponse

from .config import MAX_UPLOAD_SIZE_MB, UPLOAD_DIR


async def save_upload(file: UploadFile) -> tuple[str, str]:
    """Reads an uploaded file, enforces the size limit, and writes it to disk
    under a random filename. Returns (original_filename, stored_filename)."""
    contents = await file.read()
    if len(contents) > MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail=f"حجم فایل نباید بیشتر از {MAX_UPLOAD_SIZE_MB} مگابایت باشد",
        )

    original_name = file.filename or "upload"
    extension = Path(original_name).suffix
    stored_name = f"{uuid.uuid4().hex}{extension}"
    (UPLOAD_DIR / stored_name).write_bytes(contents)
    return original_name, stored_name


def build_download_response(
    stored_filename: Optional[str], original_filename: Optional[str]
) -> FileResponse:
    """Turns a (stored_filename, original_filename) pair from any of the
    file-carrying models into the actual file response, or raises 404."""
    if not stored_filename:
        raise HTTPException(status_code=404, detail="فایلی برای این مورد ثبت نشده است")

    path = UPLOAD_DIR / stored_filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="فایل روی سرور یافت نشد")

    return FileResponse(path, filename=original_filename)
