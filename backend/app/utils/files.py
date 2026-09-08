from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile

from app.config import ALLOWED_EXTENSIONS, MAX_UPLOAD_BYTES, UPLOAD_DIR

CHUNK_SIZE = 1024 * 1024


def save_upload(upload: UploadFile) -> dict:
    original_name = Path(upload.filename or "").name
    suffix = Path(original_name).suffix.lower()

    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Only MP3 and WAV files are allowed.",
        )

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    saved_name = f"{uuid4().hex}{suffix}"
    destination = UPLOAD_DIR / saved_name

    size_bytes = 0
    try:
        with destination.open("wb") as buffer:
            while True:
                chunk = upload.file.read(CHUNK_SIZE)
                if not chunk:
                    break
                size_bytes += len(chunk)
                if size_bytes > MAX_UPLOAD_BYTES:
                    raise HTTPException(
                        status_code=400,
                        detail="File is larger than 50 MB.",
                    )
                buffer.write(chunk)
    except HTTPException:
        destination.unlink(missing_ok=True)
        raise

    if size_bytes == 0:
        destination.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail="File is empty.")

    return {
        "filename": original_name,
        "saved_as": saved_name,
        "size_bytes": size_bytes,
        "content_type": upload.content_type,
    }