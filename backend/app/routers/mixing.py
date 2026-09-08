from fastapi import APIRouter, File, HTTPException, UploadFile

from app.config import OPENAI_API_KEY, UPLOAD_DIR
from app.services.mixing.analyzer import analyze_mix
from app.utils.files import save_upload

router = APIRouter(prefix="/api/mixing", tags=["mixing"])


@router.get("/status")
def mixing_status():
    return {
        "phase": 7,
        "loudness": True,
        "frequency": True,
        "dynamics": True,
        "stereo": True,
        "clipping": True,
        "scoring": True,
        "ai_report": bool(OPENAI_API_KEY),
        "message": "Mixing Phase 7: DSP scores plus optional AI mixing report.",
    }


@router.post("/run")
def run_mixing_analysis(file: UploadFile = File(...)):
    saved = save_upload(upload=file)
    path = UPLOAD_DIR / saved["saved_as"]
    try:
        analysis = analyze_mix(path)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Mixing analysis failed.") from exc
    finally:
        path.unlink(missing_ok=True)

    return {
        "file": {
            "filename": saved["filename"],
            "size_bytes": saved["size_bytes"],
            "content_type": saved["content_type"],
        },
        **analysis,
    }