from pathlib import Path
import os

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_DIR.parent
load_dotenv(BACKEND_DIR / ".env")

_DEFAULT_FRONTEND_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:4173",
    "http://127.0.0.1:4173",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]


def _frontend_origins():
    extras = [
        item.strip().rstrip("/")
        for item in os.getenv("FRONTEND_ORIGINS", "").split(",")
        if item.strip()
    ]
    if "*" in extras:
        return ["*"]
    origins = []
    for origin in extras + _DEFAULT_FRONTEND_ORIGINS:
        if origin and origin not in origins:
            origins.append(origin)
    return origins


FRONTEND_ORIGINS = _frontend_origins()
FRONTEND_DIST = Path(
    os.getenv("FRONTEND_DIST", str(PROJECT_ROOT / "frontend" / "dist"))
)

_ON_RAILWAY = bool(
    os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("RAILWAY_ENVIRONMENT_NAME")
)
UPLOAD_DIR = Path("/tmp/uploads") if _ON_RAILWAY else (BACKEND_DIR / "uploads")
LIBRARY_DIR = BACKEND_DIR / "library"
LIBRARY_DB = LIBRARY_DIR / "library.sqlite"
LIBRARY_AUDIO_DIR = LIBRARY_DIR / "audio"
MAX_UPLOAD_BYTES = 50 * 1024 * 1024
ALLOWED_EXTENSIONS = {".mp3", ".wav"}

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
