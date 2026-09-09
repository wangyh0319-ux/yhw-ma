from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import FRONTEND_DIST, FRONTEND_ORIGINS
from app.routers import analyze, health, library, mixing

app = FastAPI(title="AI Music Analyzer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(analyze.router)
app.include_router(mixing.router)
app.include_router(library.router)

_FRONTEND_READY = FRONTEND_DIST.is_dir() and (FRONTEND_DIST / "index.html").is_file()
_ASSETS_DIR = FRONTEND_DIST / "assets"

if _FRONTEND_READY and _ASSETS_DIR.is_dir():
    app.mount("/assets", StaticFiles(directory=str(_ASSETS_DIR)), name="frontend-assets")


def _safe_frontend_file(relative_path: str):
    if not _FRONTEND_READY or not relative_path:
        return None
    candidate = (FRONTEND_DIST / relative_path).resolve()
    root = FRONTEND_DIST.resolve()
    if candidate != root and root not in candidate.parents:
        return None
    if candidate.is_file():
        return candidate
    return None


if _FRONTEND_READY:

    @app.get("/")
    def serve_frontend_index():
        return FileResponse(FRONTEND_DIST / "index.html")

    @app.get("/{full_path:path}")
    def serve_frontend_file(full_path: str):
        if full_path == "health" or full_path.startswith("api/"):
            from fastapi import HTTPException

            raise HTTPException(status_code=404, detail="Not found.")
        target = _safe_frontend_file(full_path)
        if target is not None:
            return FileResponse(target)
        return FileResponse(FRONTEND_DIST / "index.html")
