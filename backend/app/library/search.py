import json

from app.library.db import list_tracks_for_match
from app.library.explain import explain_matches
from app.library.matching import missing_label_hint, rank_tracks
from app.library.parse_scene import parse_scene_text
from app.library.tagging import drama_tags_from_text


def _overlay_text_tags(track):
    extra = drama_tags_from_text(track.get("title") or "", "")
    tags = dict(track.get("tags") or {})
    for namespace, values in extra.items():
        current = list(tags.get(namespace) or [])
        for item in values:
            if item not in current:
                current.append(item)
        tags[namespace] = current
    copy = dict(track)
    copy["tags"] = tags
    raw = track.get("analyzer_json")
    if isinstance(raw, str) and len(raw) > 400:
        try:
            parsed = json.loads(raw)
            copy["analyzer_json"] = json.dumps(
                {
                    "bpm": parsed.get("bpm"),
                    "key": parsed.get("key"),
                    "lufs": parsed.get("lufs"),
                    "dynamic_range_db": parsed.get("dynamic_range_db"),
                }
            )
        except Exception:
            copy["analyzer_json"] = None
    return copy


def _public_track(track):
    tags = track.get("tags") or {}
    return {
        "id": track.get("id"),
        "title": track.get("title"),
        "artist": track.get("artist"),
        "audio_path": track.get("audio_path"),
        "bpm": track.get("bpm"),
        "key": track.get("key"),
        "genre": track.get("genre"),
        "energy": track.get("energy"),
        "mix_overall": track.get("mix_overall"),
        "tags": {
            "mood": tags.get("mood") or [],
            "style": tags.get("style") or [],
            "scene": tags.get("scene") or [],
            "relationship": tags.get("relationship") or [],
            "drama_function": tags.get("drama_function") or [],
        },
    }


def search_scene(text: str) -> dict:
    parsed = parse_scene_text(text)
    query = parsed["query"]
    tracks = [_overlay_text_tags(track) for track in list_tracks_for_match()]
    mode, ranked = rank_tracks(query, tracks)
    explained = explain_matches(parsed["scene"], query, ranked)
    matches = []
    for item in explained:
        matches.append(
            {
                "track": _public_track(item["track"]),
                "overall": item["overall"],
                "parts": item["parts"],
                "reason": item.get("reason"),
                "mix_overall": item["track"].get("mix_overall"),
            }
        )
    if mode == "top":
        message = None
        heading = "TOP MATCHES"
    else:
        heading = "CLOSEST MATCHES"
        hint = missing_label_hint(query)
        message = (
            "No strong matches found. Try broadening your scene description. "
            "目前音乐库中缺少非常符合「{}」的音乐。".format(hint)
        )
    return {
        "scene": parsed["scene"],
        "query": query,
        "mode": mode,
        "heading": heading,
        "message": message,
        "matches": matches,
    }
