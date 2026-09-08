import json

from app.config import LIBRARY_DIR
from app.library.db import get_tags, get_track, replace_tags, update_analysis
from app.library.lyrics import load_lyrics_snippet
from app.library.tagging import interpret_drama
from app.services.audio import analyze_audio


def _tempo_feel(bpm):
    if bpm is None:
        return None
    if bpm < 80:
        return "Slow"
    if bpm <= 110:
        return "Moderate"
    return "Driving"


def tag_library_track(track_id: str, reuse: bool = True) -> dict:
    track = get_track(track_id)
    if track is None:
        raise ValueError("Track not found.")
    if not track.get("audio_path"):
        raise ValueError("Track has no audio file.")

    path = LIBRARY_DIR / track["audio_path"]
    analysis = None
    if reuse and track.get("analyzer_json"):
        try:
            analysis = json.loads(track["analyzer_json"])
        except Exception:
            analysis = None
    if not analysis:
        analysis = analyze_audio(path)
    title = track.get("title") or ""
    lyrics = load_lyrics_snippet(path, title=title)
    drama = interpret_drama(analysis, title=title, lyrics=lyrics)
    tempo_feel = drama.get("tempo_feel") or _tempo_feel(analysis.get("bpm"))
    update_analysis(
        track_id,
        bpm=analysis.get("bpm"),
        key=analysis.get("key"),
        duration_sec=analysis.get("duration_sec"),
        genre=drama.get("genre"),
        vocal_type=drama.get("vocal_type"),
        energy=drama.get("energy"),
        tempo_feel=tempo_feel,
        brightness=drama.get("brightness"),
        tension=drama.get("tension"),
        intensity=drama.get("intensity"),
        lufs=analysis.get("lufs"),
        dynamic_range_db=analysis.get("dynamic_range_db"),
        analyzer_json=json.dumps(analysis),
        ai_description=drama.get("ai_description"),
        usage_suggestions=drama.get("usage_suggestions"),
    )
    replace_tags(track_id, drama.get("tags") or {})
    result = get_track(track_id)
    result["tags"] = get_tags(track_id)
    result["tagging"] = {
        "available": drama.get("available"),
        "message": drama.get("message"),
    }
    return result


def tag_all_library_tracks(only_missing: bool = True) -> dict:
    from app.library.db import list_tracks

    tagged = 0
    skipped = 0
    failed = []
    for track in list_tracks():
        if not track.get("audio_path"):
            continue
        has_tags = bool((track.get("tags") or {}).get("mood") or (track.get("tags") or {}).get("style") or track.get("genre"))
        if only_missing and has_tags:
            skipped += 1
            continue
        try:
            tag_library_track(track["id"])
            tagged += 1
        except Exception as extra:
            failed.append(
                {
                    "id": track["id"],
                    "title": track.get("title"),
                    "error": str(extra),
                }
            )
    return {"tagged": tagged, "skipped": skipped, "failed": failed}