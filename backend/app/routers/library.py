from pathlib import Path

from typing import List, Optional

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.config import LIBRARY_DIR
from app.library.db import (
    create_track,
    delete_track,
    get_track,
    init_db,
    list_tracks,
    update_audio,
)
from app.library.pipeline import tag_all_library_tracks, tag_library_track
from app.library.parse_scene import SceneParseError, parse_scene_text
from app.library.search import search_scene
from app.library.scene_query import sanitize_scene_query, scene_query_schema
from app.library.storage import save_library_audio
from app.library.taxonomy import taxonomy_payload

router = APIRouter(prefix="/api/library", tags=["library"])
init_db()


class TrackCreate(BaseModel):
    title: str
    artist: str = ""


class SceneParseBody(BaseModel):
    text: str = ""


@router.get("/taxonomy")
def library_taxonomy():
    return taxonomy_payload()


@router.get("/scene-query/schema")
def library_scene_query_schema():
    return scene_query_schema()


@router.post("/scene-query/clean")
def library_scene_query_clean(payload: dict):
    return sanitize_scene_query(payload)


@router.post("/scene-query/parse")
def library_scene_query_parse(payload: SceneParseBody):
    try:
        return parse_scene_text(payload.text)
    except SceneParseError as extra:
        raise HTTPException(status_code=400, detail=str(extra)) from extra


@router.post("/search/scene")
def library_search_scene(payload: SceneParseBody):
    try:
        return search_scene(payload.text)
    except SceneParseError as extra:
        raise HTTPException(status_code=400, detail=str(extra)) from extra


@router.get("/tracks")
def library_tracks(
    mood: Optional[List[str]] = Query(None),
    style: Optional[List[str]] = Query(None),
):
    return {"tracks": list_tracks(moods=mood, styles=style)}


@router.post("/tracks")
def library_create(payload: TrackCreate):
    return create_track(title=payload.title, artist=payload.artist)


@router.post("/tracks/upload")
def library_upload(
    file: UploadFile = File(...),
    title: str = Form(""),
    artist: str = Form(""),
):
    filename = Path(file.filename or "").stem
    track = create_track(title=title or filename, artist=artist)
    try:
        saved = save_library_audio(upload=file, track_id=track["id"])
        return update_audio(
            track["id"],
            saved["audio_path"],
            saved["duration_sec"],
            saved["sample_rate"],
        )
    except Exception:
        delete_track(track["id"])
        raise


@router.post("/tracks/tag-all")
def library_tag_all():
    return tag_all_library_tracks()


@router.get("/tracks/{track_id}")
def library_get(track_id: str):
    track = get_track(track_id)
    if track is None:
        raise HTTPException(status_code=404, detail="Track not found.")
    return track


@router.get("/tracks/{track_id}/audio")
def library_audio(track_id: str):
    track = get_track(track_id)
    if track is None or not track.get("audio_path"):
        raise HTTPException(status_code=404, detail="Audio not found.")
    path = (LIBRARY_DIR / track["audio_path"]).resolve()
    library_root = LIBRARY_DIR.resolve()
    if library_root not in path.parents and path != library_root:
        raise HTTPException(status_code=404, detail="Audio not found.")
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Audio not found.")
    return FileResponse(path)


@router.post("/tracks/{track_id}/tag")
def library_tag(track_id: str):
    try:
        return tag_library_track(track_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as extra:
        raise HTTPException(status_code=500, detail="Tagging failed.") from extra


@router.delete("/tracks/{track_id}")
def library_delete(track_id: str):
    if not delete_track(track_id):
        raise HTTPException(status_code=404, detail="Track not found.")
    return {"ok": True}
