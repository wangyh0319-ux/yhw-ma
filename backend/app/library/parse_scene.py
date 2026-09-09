import json

import httpx

from app.config import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL
from app.library.scene_query import sanitize_scene_query
from app.library.tagging import drama_tags_from_text
from app.library.taxonomy import ENERGY, LEVEL, NAMESPACES, TEMPO_FEEL


class SceneParseError(ValueError):
    pass


MOOD_HINTS = (
    ("Sad", ("哭", "失望", "悲伤", "难过", "泪", "心痛")),
    ("Lonely", ("一个人", "独自", "孤独")),
    ("Nostalgic", ("多年后", "想起", "前任", "曾经", "回忆")),
    ("Melancholic", ("沉默", "没有说话", "遗憾", "擦肩")),
    ("Romantic", ("告白", "表白", "拥抱", "夕阳", "恋爱")),
    ("Angry", ("争吵", "吵架", "愤怒", "摔门")),
    ("Tense", ("激烈", "冲突")),
    ("Healing", ("治愈", "释然", "和好")),
    ("Flirty", ("暧昧",)),
    ("Warm", ("温暖", "夕阳")),
)


def guess_scene_from_text(text: str) -> dict:
    drama = drama_tags_from_text(text, "")
    moods = []
    for tag, needles in MOOD_HINTS:
        if any(needle in text for needle in needles) and tag not in moods:
            moods.append(tag)
    energy = None
    tempo_feel = None
    tempo_range = None
    tension = None
    intensity = None
    if any(word in text for word in ("争吵", "激烈", "高潮", "转身离开")):
        energy = "High"
        tempo_feel = "Driving"
        tension = "High"
        intensity = "High"
        tempo_range = [100, 140]
    elif any(word in text for word in ("雨", "医院", "去世", "沉默", "失望", "凌晨")):
        energy = "Low"
        tempo_feel = "Slow"
        tension = "Low"
        intensity = "Low"
        tempo_range = [60, 90]
    elif any(word in text for word in ("告白", "拥抱")):
        energy = "Medium"
        tempo_feel = "Moderate"
        tension = "Low"
        intensity = "Medium"
        tempo_range = [70, 110]
    raw = {
        "mood": moods,
        "scene": drama.get("scene") or [],
        "relationship": drama.get("relationship") or [],
        "drama_function": drama.get("drama_function") or [],
        "energy": energy,
        "tension": tension,
        "intensity": intensity,
        "tempo_feel": tempo_feel,
        "tempo_range": tempo_range,
    }
    return sanitize_scene_query(raw)


def _llm_scene_query(scene: str):
    payload = {
        "model": OPENAI_MODEL,
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
        "messages": [
            {
                "role": "system",
                "content": (
                    "You convert a short-drama scene description into a music search query. "
                    "Use only the provided English enums. Do not invent tags. "
                    "Prefer 1-3 items per list. Leave a field null or [] if unsure. "
                    "JSON keys: mood, scene, relationship, drama_function (arrays), "
                    "energy, tension, intensity (each one of {level} or null), "
                    "tempo_feel (one of {tempo} or null), "
                    "tempo_range ([min_bpm, max_bpm] or null)."
                ).format(level=list(LEVEL), tempo=list(TEMPO_FEEL))
                + " Allowed mood: {mood}. scene: {scene}. relationship: {rel}. "
                "drama_function: {fn}. energy: {energy}.".format(
                    mood=list(NAMESPACES["mood"]),
                    scene=list(NAMESPACES["scene"]),
                    rel=list(NAMESPACES["relationship"]),
                    fn=list(NAMESPACES["drama_function"]),
                    energy=list(ENERGY),
                ),
            },
            {"role": "user", "content": scene},
        ],
    }
    response = httpx.post(
        f"{OPENAI_BASE_URL}/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=20.0,
    )
    response.raise_for_status()
    parsed = json.loads(response.json()["choices"][0]["message"]["content"])
    if not isinstance(parsed, dict):
        raise ValueError("bad json")
    return sanitize_scene_query(parsed)


def parse_scene_text(text: str) -> dict:
    scene = (text or "").strip()
    if not scene:
        raise SceneParseError("Describe your scene first.")
    rules = guess_scene_from_text(scene)
    if not OPENAI_API_KEY:
        return {
            "scene": scene,
            "query": rules,
            "available": True,
            "source": "rules",
            "message": "Parsed without OpenAI (no paid API needed).",
        }
    try:
        query = _llm_scene_query(scene)
        return {
            "scene": scene,
            "query": query,
            "available": True,
            "source": "ai",
            "message": None,
        }
    except Exception:
        return {
            "scene": scene,
            "query": rules,
            "available": True,
            "source": "rules",
            "message": "OpenAI unavailable or out of credit. Used keyword parsing instead.",
        }
