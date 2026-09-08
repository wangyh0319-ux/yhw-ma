import json
import re

import httpx

from app.config import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL
from app.library.taxonomy import (
    ENERGY,
    GENRE,
    LEVEL,
    NAMESPACES,
    TEMPO_FEEL,
    VOCAL_TYPE,
)


# Title-only: single Chinese characters are OK here, not in lyrics.
# First matching genre wins; moods from every title match are merged.
TITLE_HINTS = (
    (("治愈", "阳光", "希望", "heal"), ("Healing", "Warm"), "Pop"),
    (("雨", "night", "夜"), ("Lonely", "Sad"), "Ambient"),
    (("星", "光", "浪漫", "甜", "温柔"), ("Romantic", "Warm"), "Pop"),
    (("以后", "如果", "回忆", "曾经", "昨天", "那年", "memory"), ("Nostalgic", "Sad"), "Pop"),
    (("借", "一个人", "alone", "想你", "失去", "离开", "走后", "分手"), ("Lonely", "Sad"), "Pop"),
    (("爱", "love", "恋"), ("Romantic", "Flirty"), "Pop"),
    (("山", "海", "风", "远方"), ("Warm", "Nostalgic"), "Cinematic"),
)

# Lyrics: longer / clearer emotion words only. Do not match 雨/夜/风/山/海/光/爱 alone.
LYRIC_HINTS = (
    (("治愈", "释然", "希望", "阳光"), ("Healing", "Warm")),
    (("眼泪", "哭泣", "心碎", "心痛", "难过", "思念", "寂寞", "孤独", "想念", "告别"), ("Lonely", "Sad")),
    (("拥抱", "温柔", "恋爱", "我爱你", "亲吻"), ("Romantic", "Warm")),
    (("回忆", "曾经", "那年", "从前"), ("Nostalgic", "Sad")),
)

# Title may use short words. Lyrics need clearer phrases so 不恨你 / 恨不得 / 别紧张
# and English substrings (dangerous, courage, intense) do not flip the song.
TITLE_AGGRESSIVE = (
    (("恨", "怒", "愤怒", "仇恨"), ("Angry", "Tense")),
    (("压迫", "压抑"), ("Oppressive", "Tense")),
    (("冲突", "紧张"), ("Tense",)),
)
LYRIC_AGGRESSIVE = (
    (("我恨", "恨你", "怨恨", "仇恨", "憎恶", "愤怒", "怒火"), ("Angry", "Tense")),
    (("压迫", "压抑", "窒息"), ("Oppressive", "Tense")),
    (("冲突",), ("Tense",)),
)
EN_AGGRESSIVE = (
    (r"\bhate\b", ("Angry", "Tense")),
    (r"\bangry\b", ("Angry", "Tense")),
    (r"\banger\b", ("Angry", "Tense")),
    (r"\brage\b", ("Angry", "Tense")),
    (r"\brevenge\b", ("Angry", "Tense")),
    (r"\btense\b", ("Tense",)),
    (r"\bconflict\b", ("Tense",)),
    (r"\boppress", ("Oppressive", "Tense")),
)
NEGATING_PREFIXES = ("不", "别", "没")
AGGRESSIVE_MOODS = ("Angry", "Tense", "Oppressive")


def _keep(allowed, values, limit=4):
    allowed_set = set(allowed)
    cleaned = []
    for value in values or []:
        if value in allowed_set and value not in cleaned:
            cleaned.append(value)
        if len(cleaned) >= limit:
            break
    return cleaned


def _pick_one(allowed, value):
    if value in allowed:
        return value
    return None


def _contains_any(text: str, needles) -> bool:
    return any(needle.lower() in text for needle in needles)


def _has_phrase(text: str, phrase: str) -> bool:
    start = 0
    needle = phrase.lower()
    hay = text
    while True:
        index = hay.find(needle, start)
        if index < 0:
            return False
        prefix = hay[max(0, index - 1) : index]
        if prefix not in NEGATING_PREFIXES:
            return True
        start = index + 1


def _moods_from_pairs(text: str, pairs, use_phrase=False):
    found = []
    if not text:
        return found
    for needles, moods in pairs:
        matched = False
        for needle in needles:
            if use_phrase and _has_phrase(text, needle):
                matched = True
                break
            if not use_phrase and needle.lower() in text:
                matched = True
                break
        if matched:
            for mood in moods:
                if mood not in found:
                    found.append(mood)
    return found


def _aggressive_from_text(title: str, lyrics: str) -> list:
    title_text = (title or "").lower()
    lyric_text = (lyrics or "").lower()
    found = []
    for extra in (
        _moods_from_pairs(title_text, TITLE_AGGRESSIVE, use_phrase=True),
        _moods_from_pairs(lyric_text, LYRIC_AGGRESSIVE, use_phrase=True),
    ):
        for mood in extra:
            if mood not in found:
                found.append(mood)
    combined = " ".join(part for part in (title_text, lyric_text) if part)
    for pattern, moods in EN_AGGRESSIVE:
        if _has_en_word(combined, pattern):
            for mood in moods:
                if mood not in found:
                    found.append(mood)
    return found


def _has_en_word(text: str, pattern: str) -> bool:
    for match in re.finditer(pattern, text, flags=re.IGNORECASE):
        prefix = text[max(0, match.start() - 12) : match.start()].lower()
        if re.search(r"(n't|not|never|no)\s*$", prefix.strip()):
            continue
        return True
    return False


def _is_aggressive_spectrum(analysis: dict) -> bool:
    bpm = analysis.get("bpm") or 0
    if bpm < 128:
        return False
    bands = (analysis.get("spectrum") or {}).get("bands") or {}
    mid = bands.get("mid")
    high_mid = bands.get("high_mid")
    high = bands.get("high")
    if mid is None:
        return False
    harsh = False
    if high_mid is not None:
        harsh = high_mid >= mid - 3
    if high is not None:
        harsh = harsh or high >= mid - 2
    if not harsh:
        return False
    rms_db = analysis.get("rms_db")
    lufs = analysis.get("lufs")
    loud = (rms_db is not None and rms_db >= -11) or (lufs is not None and lufs >= -9)
    return bool(loud)


def _baseline_moods(minor: bool, bpm: float) -> list:
    if minor:
        if bpm < 85:
            return ["Lonely", "Melancholic"]
        if bpm < 120:
            return ["Sad", "Melancholic"]
        return ["Nostalgic", "Melancholic"]
    if bpm < 110:
        return ["Warm", "Healing"]
    if bpm < 125:
        return ["Warm", "Romantic"]
    return ["Warm", "Flirty"]


def _merge_moods(base, extra):
    merged = list(extra)
    for item in base:
        if item not in merged:
            merged.append(item)
    return merged


def _apply_title_hints(moods, genre, title: str):
    text = (title or "").lower()
    if not text:
        return moods, genre
    extra_moods = []
    picked_genre = genre
    for needles, hint_moods, hint_genre in TITLE_HINTS:
        if not _contains_any(text, needles):
            continue
        for mood in hint_moods:
            if mood not in extra_moods:
                extra_moods.append(mood)
        if hint_genre and picked_genre == genre:
            picked_genre = hint_genre
    if extra_moods:
        moods = _merge_moods(moods, extra_moods)
    return moods, picked_genre


def _apply_lyric_hints(moods, lyrics: str):
    text = (lyrics or "").lower()
    if not text:
        return moods
    extra_moods = []
    for needles, hint_moods in LYRIC_HINTS:
        if not _contains_any(text, needles):
            continue
        for mood in hint_moods:
            if mood not in extra_moods:
                extra_moods.append(mood)
    if extra_moods:
        appended = list(moods)
        for mood in extra_moods:
            if mood not in appended:
                appended.append(mood)
        return appended
    return moods


def guess_from_analysis(analysis: dict, title: str = "", lyrics: str = "") -> dict:
    bpm = analysis.get("bpm") or 0
    key = (analysis.get("key") or "").lower()
    bands = (analysis.get("spectrum") or {}).get("bands") or {}
    bass = bands.get("bass") or -80
    sub = bands.get("sub") or -80
    mid = bands.get("mid") or -80
    high = bands.get("high") or -80
    high_mid = bands.get("high_mid") or -80
    minor = "minor" in key
    aggressive_moods = _aggressive_from_text(title, lyrics)
    aggressive_sound = _is_aggressive_spectrum(analysis)

    if bpm >= 125 and (sub > mid - 5 or bass > high_mid):
        genre = "Electronic"
    elif bpm >= 118:
        genre = "Pop"
    elif bpm < 80 and high < mid:
        genre = "Ambient"
    elif bass > high_mid + 8 and bpm < 110:
        genre = "R&B"
    elif bpm < 100:
        genre = "Cinematic"
    else:
        genre = "Pop"

    moods = _baseline_moods(minor, bpm)
    moods, genre = _apply_title_hints(moods, genre, title)
    moods = _apply_lyric_hints(moods, lyrics)

    if aggressive_moods:
        moods = _merge_moods(
            [item for item in moods if item not in AGGRESSIVE_MOODS],
            aggressive_moods,
        )
    elif aggressive_sound:
        moods = _merge_moods(
            [item for item in moods if item not in ("Tense", "Angry")],
            ["Tense", "Angry"],
        )

    if bpm < 80:
        tempo = "Slow"
        energy = "Low"
        brightness = "Low"
        tension = "High" if (aggressive_moods or aggressive_sound) else "Low"
        intensity = "Low"
    elif bpm <= 110:
        tempo = "Moderate"
        energy = "Medium"
        brightness = "Medium"
        tension = "High" if (aggressive_moods or aggressive_sound) else "Low"
        intensity = "Medium"
    else:
        tempo = "Driving"
        energy = "High"
        brightness = "High"
        tension = "High" if (aggressive_moods or aggressive_sound) else "Medium"
        intensity = "High"

    moods = _keep(NAMESPACES["mood"], moods, limit=3)
    return {
        "available": True,
        "genre": genre if genre in GENRE else None,
        "vocal_type": "Instrumental",
        "energy": energy,
        "tempo_feel": tempo,
        "brightness": brightness,
        "tension": tension,
        "intensity": intensity,
        "tags": {
            "mood": moods,
            "style": _keep(GENRE, [genre]),
            "drama_function": [],
            "relationship": [],
            "scene": [],
        },
        "ai_description": None,
        "usage_suggestions": None,
        "message": None,
        "source": "rules",
    }


def interpret_drama(analysis: dict, title: str = "", lyrics: str = "") -> dict:
    snippet = (lyrics or "")[:2000]
    guessed = guess_from_analysis(analysis, title=title, lyrics=snippet)
    if not OPENAI_API_KEY:
        guessed["message"] = (
            "Tags from audio, title, and lyrics rules. Set OPENAI_API_KEY for richer drama tags."
        )
        return guessed

    payload = {
        "model": OPENAI_MODEL,
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
        "messages": [
            {
                "role": "system",
                "content": (
                    "You tag music for short-drama scoring. Use only provided enums. "
                    "Do not invent tags. Prefer 1-3 tags per list. "
                    "Do not overuse Oppressive or Tense. Match the song's emotional color. "
                    "Most minor-key C-pop ballads are sad, nostalgic, lonely, romantic, warm, or healing — not oppressive. "
                    "Lyrics and title outweigh spectrum for mood. "
                    "Reserve Tense, Oppressive, and Angry for clear lyric/title evidence "
                    "(恨/怒/压迫/冲突/紧张 or equivalent) or clearly aggressive music. "
                    "JSON keys: genre/style (one of {genre}), vocal_type (one of {vocal}), "
                    "energy (one of {energy}), tempo_feel (one of {tempo}), "
                    "brightness, tension, intensity (each one of {level}), "
                    "mood, drama_function, relationship, scene (arrays), "
                    "ai_description, usage_suggestions (short Chinese or English sentences)."
                ).format(
                    genre=list(GENRE),
                    vocal=list(VOCAL_TYPE),
                    energy=list(ENERGY),
                    tempo=list(TEMPO_FEEL),
                    level=list(LEVEL),
                )
                + " Allowed mood: {mood}. drama_function: {fn}. relationship: {rel}. scene: {scene}.".format(
                    mood=list(NAMESPACES["mood"]),
                    fn=list(NAMESPACES["drama_function"]),
                    rel=list(NAMESPACES["relationship"]),
                    scene=list(NAMESPACES["scene"]),
                ),
            },
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "title": title,
                        "lyrics": snippet or None,
                        "bpm": analysis.get("bpm"),
                        "key": analysis.get("key"),
                        "duration_sec": analysis.get("duration_sec"),
                        "lufs": analysis.get("lufs"),
                        "rms_db": analysis.get("rms_db"),
                        "dynamic_range_db": analysis.get("dynamic_range_db"),
                        "spectrum_bands": analysis.get("spectrum", {}).get("bands"),
                    }
                ),
            },
        ],
    }

    try:
        response = httpx.post(
            f"{OPENAI_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=45.0,
        )
        response.raise_for_status()
        parsed = json.loads(response.json()["choices"][0]["message"]["content"])
    except Exception:
        guessed["message"] = "AI tagging failed. Used audio + title + lyrics rules instead."
        return guessed

    genre = _pick_one(GENRE, parsed.get("genre") or parsed.get("style")) or guessed["genre"]
    tags = {
        name: _keep(allowed, parsed.get(name))
        for name, allowed in NAMESPACES.items()
    }
    if not tags.get("mood"):
        tags["mood"] = guessed["tags"]["mood"]
    tags["style"] = _keep(GENRE, [genre] + (parsed.get("style") or []))
    if not tags["style"] and genre:
        tags["style"] = [genre]
    return {
        "available": True,
        "genre": genre,
        "vocal_type": _pick_one(VOCAL_TYPE, parsed.get("vocal_type")) or guessed["vocal_type"],
        "energy": _pick_one(ENERGY, parsed.get("energy")) or guessed["energy"],
        "tempo_feel": _pick_one(TEMPO_FEEL, parsed.get("tempo_feel")) or guessed["tempo_feel"],
        "brightness": _pick_one(LEVEL, parsed.get("brightness")) or guessed["brightness"],
        "tension": _pick_one(LEVEL, parsed.get("tension")) or guessed["tension"],
        "intensity": _pick_one(LEVEL, parsed.get("intensity")) or guessed["intensity"],
        "tags": tags,
        "ai_description": parsed.get("ai_description")
        if isinstance(parsed.get("ai_description"), str)
        else None,
        "usage_suggestions": parsed.get("usage_suggestions")
        if isinstance(parsed.get("usage_suggestions"), str)
        else None,
        "message": None,
        "source": "ai",
    }
