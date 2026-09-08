from pathlib import Path

import librosa
from fastapi import HTTPException, UploadFile

from app.config import ALLOWED_EXTENSIONS, LIBRARY_AUDIO_DIR, MAX_UPLOAD_BYTES

CHUNK_SIZE = 1024 * 1024


def save_library_audio(upload: UploadFile, track_id: str) -> dict:
    original_name = Path(upload.filename or "").name
    suffix = Path(original_name).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Only MP3 and WAV files are allowed.",
        )

    LIBRARY_AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    saved_name = f"{track_id}{suffix}"
    destination = LIBRARY_AUDIO_DIR / saved_name

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

    duration_sec = None
    sample_rate = None
    try:
        duration_sec = round(float(librosa.get_duration(filename=str(destination))), 3)
        sample_rate = int(librosa.get_samplerate(str(destination)))
    except Exception:
        pass

    return {
        "filename": original_name,
        "audio_path": f"audio/{saved_name}",
        "duration_sec": duration_sec,
        "sample_rate": sample_rate,
    }