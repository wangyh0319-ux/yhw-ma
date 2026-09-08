from fastapi import APIRouter, File, HTTPException, UploadFile

from app.config import OPENAI_API_KEY, UPLOAD_DIR
from app.services.ai import classify_track
from app.services.audio import analyze_audio
from app.services.report import build_report
from app.utils.files import save_upload

router = APIRouter(prefix="/api/analyze", tags=["analyze"])


@router.get("/status")
def analyze_status():
    return {
        "upload": True,
        "analysis": True,
        "ai": bool(OPENAI_API_KEY),
        "message": "Upload, librosa analysis, and optional AI labels are available.",
    }


@router.post("/upload")
def upload_audio(file: UploadFile = File(...)):
    return save_upload(upload=file)


@router.post("/run")
def run_analysis(file: UploadFile = File(...)):
    saved = save_upload(upload=file)
    path = UPLOAD_DIR / saved["saved_as"]
    try:
        analysis = analyze_audio(path)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Analysis failed.") from exc
    finally:
        path.unlink(missing_ok=True)

    return build_report(saved, analysis, classify_track(analysis))
