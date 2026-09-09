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
# Moods from every title match are merged. Style is decided separately.
TITLE_HINTS = (
    (("治愈", "阳光", "希望", "heal"), ("Healing", "Warm")),
    (("雨", "night", "夜"), ("Lonely", "Sad")),
    (("星", "光", "浪漫", "甜", "温柔"), ("Romantic", "Warm")),
    (("以后", "如果", "回忆", "曾经", "昨天", "那年", "memory"), ("Nostalgic", "Sad")),
    (("借", "一个人", "alone", "想你", "失去", "离开", "走后", "分手"), ("Lonely", "Sad")),
    (("爱", "love", "恋"), ("Romantic", "Flirty")),
    (("山", "海", "风", "远方"), ("Warm", "Nostalgic")),
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

# Styles that must not be assigned from BPM/bass alone.
EVIDENCE_STYLES = (
    "HipHop",
    "Rock",
    "Electronic",
    "R&B",
    "SynthPop",
    "LoFi",
    "GuFeng",
    "Piano",
    "Orchestral",
    "Cinematic",
    "Ambient",
    "Acoustic",
    "Folk",
    "Indie",
)

# Higher wins ties so Pop/Ballad do not bury a more specific tag.
STYLE_PRIORITY = {
    "GuFeng": 16,
    "Orchestral": 15,
    "Piano": 14,
    "LoFi": 13,
    "HipHop": 12,
    "Rock": 11,
    "SynthPop": 10,
    "Electronic": 9,
    "Acoustic": 8,
    "Folk": 7,
    "Ambient": 6,
    "Cinematic": 5,
    "R&B": 4,
    "Indie": 3,
    "Ballad": 2,
    "Pop": 1,
}

# English patterns use regex word boundaries; Chinese is substring.
STYLE_TITLE_HINTS = (
    ("HipHop", ("说唱", "饶舌", "嘻哈", r"\brap\b", r"\bhip-?hop\b", r"\btrap\b")),
    ("Rock", ("摇滚", "朋克", "金属乐", r"\brock\b", r"\bpunk\b", r"\bmetal\b")),
    ("Electronic", ("电音", "电子", r"\bedm\b", r"\btechno\b", r"\btrance\b", r"\bdubstep\b")),
    ("R&B", ("节奏蓝调", r"\br&b\b", r"\brnb\b", r"\bsoul\b")),
    ("SynthPop", ("合成器", "合成流行", r"\bsynth-?pop\b", r"\bsynthpop\b")),
    ("LoFi", ("lofi", "lo-fi", "lo fi", r"\bchillhop\b")),
    ("GuFeng", ("古风", "国风", "江湖", "侠客", "长安", "汉服", "古筝", "琵琶", "戏腔", "词牌", "青丝", "红尘")),
    ("Cinematic", ("影视", "配乐", "电影", "片头", "片尾", "预告", r"\bost\b", r"\bcinematic\b", r"\btrailer\b", r"\bscore\b")),
    ("Orchestral", ("管弦", "交响", "弦乐", r"\borchestra\b", r"\borchestral\b", r"\bsymphony\b")),
    ("Piano", ("钢琴", r"\bpiano\b")),
    ("Ambient", ("氛围", "空灵", r"\bambient\b")),
    ("Acoustic", ("原声", "木吉他", r"\bacoustic\b", r"\bunplugged\b")),
    ("Folk", ("民谣", r"\bfolk\b")),
    ("Indie", ("独立音乐", r"\bindie\b")),
    ("Ballad", ("情歌", "抒情", r"\bballad\b")),
)

# Lyrics: skip production notes (piano/cinematic/soul) and metaphor (电影/红尘 alone is kept with 古风 cues).
STYLE_LYRIC_HINTS = (
    ("HipHop", ("说唱", "饶舌", "嘻哈")),
    ("Rock", ("摇滚", "朋克")),
    ("Electronic", ("电音", "电子乐")),
    ("GuFeng", ("古风", "国风", "江湖", "侠客", "长安", "汉服", "古筝", "琵琶", "戏腔", "词牌", "青丝", "红尘")),
    ("Cinematic", ("配乐", "影视")),
    ("Orchestral", ("管弦", "交响")),
    ("Folk", ("民谣",)),
    ("Ballad", ("情歌", "抒情")),
)

BALLAD_TEXT = (
    "如果",
    "以后",
    "曾经",
    "回忆",
    "昨天",
    "那年",
    "想你",
    "离开",
    "走后",
    "分手",
    "一个人",
    "情歌",
    "眼泪",
    "拥抱",
    "温柔",
    "晚安",
    "后来",
    "记得",
    "忘记",
    "星光",
    "山海",
    "月光",
    "远方",
    "借过",
    r"\bballad\b",
    r"\bgoodbye\b",
    r"\blonely\b",
    r"\bmemory\b",
    r"\bforever\b",
    r"\bquiet\b",
    r"\bheart\b",
    r"\blove\b",
    r"\baway\b",
    r"\bstay\b",
    r"\bwhisper\b",
    r"\bdistance\b",
    r"\bnothing left\b",
    r"\bletting go\b",
)

_CJK_RE = re.compile(r"[\u4e00-\u9fff]")


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


def _apply_title_hints(moods, title: str):
    text = (title or "").lower()
    if not text:
        return moods
    extra_moods = []
    for needles, hint_moods in TITLE_HINTS:
        if not _contains_any(text, needles):
            continue
        for mood in hint_moods:
            if mood not in extra_moods:
                extra_moods.append(mood)
    if extra_moods:
        return _merge_moods(moods, extra_moods)
    return moods


def _as_list(value):
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, (list, tuple)):
        return list(value)
    return []


def _has_cjk(text: str) -> bool:
    return bool(_CJK_RE.search(text or ""))


def _needle_in_text(text: str, needle: str) -> bool:
    if not text or not needle:
        return False
    if r"\b" in needle or any(ch in needle for ch in ("?", "+")):
        pattern = needle
        if r"\b" in needle:
            body = needle
            if body.startswith(r"\b"):
                body = body[2:]
            if body.endswith(r"\b"):
                body = body[:-2]
            pattern = r"(?<![A-Za-z])" + body + r"(?![A-Za-z])"
        return bool(re.search(pattern, text, flags=re.IGNORECASE))
    return needle.lower() in text


def _style_hits_from(text: str, pairs) -> list:
    found = []
    hay = (text or "").lower()
    if not hay:
        return found
    for style, needles in pairs:
        if any(_needle_in_text(hay, needle) for needle in needles):
            found.append(style)
    return found


def _text_style_hits(title: str = "", lyrics: str = "") -> list:
    found = []
    for style in _style_hits_from(title, STYLE_TITLE_HINTS) + _style_hits_from(lyrics, STYLE_LYRIC_HINTS):
        if style not in found:
            found.append(style)
    return found


DRAMA_TEXT_HINTS = {
    "scene": (
        ("Rain", ("下雨", "雨夜", "雨中", "雨停", "雨里")),
        ("Night", ("夜", "凌晨", "深夜", "夜里")),
        ("Street", ("街头", "街上", "马路", "公路", "出租")),
        ("Hospital", ("医院", "走廊")),
        ("Airport", ("机场",)),
        ("Wedding", ("婚礼", "结婚")),
        ("Campus", ("校园", "学校")),
        ("Cafe", ("咖啡",)),
        ("Office", ("公司", "办公室")),
        ("Home", ("回家", "家里")),
        ("Alone", ("一个人", "独自", "一个人的")),
    ),
    "relationship": (
        ("Betrayal", ("出轨", "背叛", "劈腿")),
        ("Reunion", ("重逢", "再次相遇")),
        ("Confession", ("告白", "表白")),
        ("Breakup", ("分手", "前任")),
        ("Misunderstanding", ("误会",)),
        ("FirstMeeting", ("初遇", "初见")),
        ("Reconciliation", ("和好", "复合")),
        ("Crush", ("暗恋",)),
        ("ColdWar", ("冷战",)),
        ("Flirting", ("暧昧",)),
    ),
    "drama_function": (
        ("Conflict", ("争吵", "吵架", "冲突", "转身离开")),
        ("Climax", ("高潮",)),
        ("Ending", ("擦肩", "结局", "最后")),
        ("Memory", ("回忆", "想起")),
        ("Build-up", ("发现",)),
        ("Reveal", ("得知", "去世")),
    ),
}


def drama_tags_from_text(title: str = "", lyrics: str = "") -> dict:
    blob = "{} {}".format(title or "", lyrics or "")
    tags = {"scene": [], "relationship": [], "drama_function": []}
    for namespace, pairs in DRAMA_TEXT_HINTS.items():
        for tag, needles in pairs:
            if any(_needle_in_text(blob, needle) for needle in needles):
                if tag not in tags[namespace]:
                    tags[namespace].append(tag)
        tags[namespace] = tags[namespace][:3]
    return tags


def _has_ballad_text(text: str) -> bool:
    hay = (text or "").lower()
    if not hay:
        return False
    return any(_needle_in_text(hay, needle) for needle in BALLAD_TEXT)


def _effective_bpm(bpm: float, title: str, lyrics: str) -> float:
    bpm = float(bpm or 0)
    if bpm >= 180:
        return bpm / 2.0
    blob = f"{title or ''} {lyrics or ''}"
    if bpm >= 136 and _has_ballad_text(blob) and not _text_style_hits(title, lyrics):
        return bpm / 2.0
    return bpm


def _add_score(scores: dict, style: str, points: float):
    if style not in GENRE or points <= 0:
        return
    scores[style] = scores.get(style, 0) + points


def _guess_styles(analysis: dict, title: str = "", lyrics: str = "") -> tuple:
    raw_bpm = float(analysis.get("bpm") or 0)
    bpm = _effective_bpm(raw_bpm, title, lyrics)
    bands = (analysis.get("spectrum") or {}).get("bands") or {}
    sub = bands.get("sub")
    bass = bands.get("bass")
    mid = bands.get("mid")
    high_mid = bands.get("high_mid")
    high = bands.get("high")
    if sub is None:
        sub = -80
    if bass is None:
        bass = -80
    if mid is None:
        mid = -80
    if high_mid is None:
        high_mid = -80
    if high is None:
        high = -80

    blob = f"{title or ''}\n{lyrics or ''}"
    text_hits = _text_style_hits(title, lyrics)
    scores = {}
    for style in text_hits:
        _add_score(scores, style, 4)
    title_text = title or ""
    if any(token in title_text for token in ("配乐", "影视", "电影")):
        _add_score(scores, "Cinematic", 1)

    sparse = high_mid > sub + 4 and bass < mid + 4
    dark = high < mid - 4
    wide_mid = mid > bass - 4 and mid > high - 2 and abs(mid - high_mid) < 14
    strong_sub = sub >= mid - 2 and sub >= 16

    if "Piano" not in text_hits and sparse and bpm < 95 and high_mid > sub + 6:
        _add_score(scores, "Piano", 2)
    if "Ambient" not in text_hits and bpm < 80 and dark and high_mid < mid - 6:
        _add_score(scores, "Ambient", 2)
    if "Cinematic" not in text_hits and wide_mid and bpm < 110 and not _has_ballad_text(blob):
        if not _has_cjk(title):
            _add_score(scores, "Cinematic", 2)
    if "Acoustic" in text_hits or "Folk" in text_hits:
        if sub < mid - 6 and not strong_sub:
            _add_score(scores, "Acoustic", 2)

    ballad_like = _has_ballad_text(blob) or (_has_cjk(title) and bpm < 100)
    if ballad_like:
        _add_score(scores, "Ballad", 2.5 if bpm < 100 else 2)
        _add_score(scores, "Pop", 1.5 if bpm >= 100 else 1)
    elif bpm < 95:
        _add_score(scores, "Ballad", 2)
        _add_score(scores, "Pop", 1)
    else:
        _add_score(scores, "Pop", 2)
        if bpm < 110:
            _add_score(scores, "Ballad", 1)

    for style in list(scores):
        if style in EVIDENCE_STYLES and style not in text_hits and scores[style] < 2:
            scores.pop(style, None)

    if "Cinematic" in scores and "Cinematic" not in text_hits and scores.get("Ballad", 0) >= 2:
        scores.pop("Cinematic", None)
    if "Orchestral" in scores and "Orchestral" not in text_hits and scores.get("Ballad", 0) >= 2:
        scores.pop("Orchestral", None)
    if "Ambient" in scores and "Ambient" not in text_hits and scores.get("Ballad", 0) >= 2:
        scores.pop("Ambient", None)

    if not scores:
        primary = "Ballad" if bpm < 95 else "Pop"
        return primary, [primary]

    ranked = sorted(
        scores.items(),
        key=lambda item: (-item[1], -STYLE_PRIORITY.get(item[0], 0)),
    )
    styles = [name for name, _ in ranked[:2]]
    return styles[0], styles


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
    raw_bpm = analysis.get("bpm") or 0
    bpm = _effective_bpm(raw_bpm, title, lyrics)
    key = (analysis.get("key") or "").lower()
    minor = "minor" in key
    aggressive_moods = _aggressive_from_text(title, lyrics)
    aggressive_sound = _is_aggressive_spectrum(analysis)
    genre, styles = _guess_styles(analysis, title=title, lyrics=lyrics)

    moods = _baseline_moods(minor, bpm)
    moods = _apply_title_hints(moods, title)
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
    drama = drama_tags_from_text(title, lyrics)
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
            "style": _keep(GENRE, styles or [genre], limit=2),
            "drama_function": drama["drama_function"],
            "relationship": drama["relationship"],
            "scene": drama["scene"],
        },
        "ai_description": None,
        "usage_suggestions": None,
        "message": None,
        "source": "rules",
    }


def _guard_ai_styles(genre, styles, guessed: dict, title: str, lyrics: str, analysis: dict):
    rule_styles = guessed.get("tags", {}).get("style") or []
    rule_genre = guessed.get("genre")
    text_hits = set(_text_style_hits(title, lyrics))
    allowed_extra = text_hits.union(rule_styles)
    cleaned = []
    for style in _keep(GENRE, _as_list(styles) + _as_list(genre), limit=4):
        if style in EVIDENCE_STYLES and style not in allowed_extra:
            continue
        if style not in cleaned:
            cleaned.append(style)
    if not cleaned:
        cleaned = list(rule_styles)
    if genre not in cleaned:
        genre = cleaned[0] if cleaned else rule_genre
    if genre and genre not in cleaned:
        cleaned = [genre] + [item for item in cleaned if item != genre]
    return genre, _keep(GENRE, cleaned, limit=2)


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
                    "genre is the primary style (one of {genre}). "
                    "style is an array of 1-2 styles from that same list. "
                    "Chinese pop titles such as 如果还有以后, 借一盏星光, 我向山海而去 are Pop or Ballad, "
                    "not HipHop, Rock, or Electronic. "
                    "Do not assign HipHop, Rock, Electronic, or R&B without title, lyric, or clear spectrum evidence. "
                    "Piano or Ambient: sparse high-mid versus sub, slow BPM. "
                    "Cinematic or Orchestral only for 影视/配乐/OST-like titles or wide mid-range score texture, "
                    "not every minor-key ballad. GuFeng is 古风/国风. "
                    "JSON keys: genre (one of {genre}), style (1-2 of {genre}), vocal_type (one of {vocal}), "
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

    ai_styles = _keep(GENRE, _as_list(parsed.get("style")) + _as_list(parsed.get("genre")), limit=2)
    ai_genre = _pick_one(GENRE, parsed.get("genre") if isinstance(parsed.get("genre"), str) else None)
    if not ai_genre and ai_styles:
        ai_genre = ai_styles[0]
    genre, styles = _guard_ai_styles(
        ai_genre or guessed["genre"],
        ai_styles,
        guessed,
        title,
        snippet,
        analysis,
    )
    tags = {
        name: _keep(allowed, parsed.get(name))
        for name, allowed in NAMESPACES.items()
    }
    if not tags.get("mood"):
        tags["mood"] = guessed["tags"]["mood"]
    tags["style"] = styles
    if not tags["style"] and genre:
        tags["style"] = [genre]
    for name in ("drama_function", "relationship", "scene"):
        if not tags.get(name):
            tags[name] = guessed["tags"].get(name) or []
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
