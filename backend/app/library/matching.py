WEIGHTS = {
    "mood": 0.30,
    "scene": 0.20,
    "relationship": 0.20,
    "drama_function": 0.15,
    "energy": 0.10,
    "tempo": 0.05,
}

LEVELS = ("Low", "Medium", "High")
TEMPO_FEEL_BPM = {
    "Slow": (0, 80),
    "Moderate": (80, 110),
    "Driving": (110, 240),
}
STRONG_OVERALL = 55.0
TOP_LIMIT = 5
CLOSEST_LIMIT = 5


def _overlap_score(wanted, have):
    wanted = [item for item in (wanted or []) if item]
    if not wanted:
        return None
    have_set = set(have or [])
    if not have_set:
        return 0.0
    hits = sum(1 for item in wanted if item in have_set)
    return round(100.0 * hits / len(wanted), 1)


def _level_score(wanted, have):
    if not wanted:
        return None
    if not have or have not in LEVELS:
        return 0.0
    if wanted == have:
        return 100.0
    distance = abs(LEVELS.index(wanted) - LEVELS.index(have))
    if distance == 1:
        return 50.0
    return 0.0


def _tempo_score(query, bpm):
    wanted_range = query.get("tempo_range")
    feel = query.get("tempo_feel")
    if wanted_range and len(wanted_range) == 2:
        if bpm is None:
            return 0.0
        low, high = wanted_range
        if low <= bpm <= high:
            return 100.0
        gap = low - bpm if bpm < low else bpm - high
        return max(0.0, round(100.0 - gap * 2.0, 1))
    if feel:
        if bpm is None:
            return 0.0
        low, high = TEMPO_FEEL_BPM.get(feel, (None, None))
        if low is None:
            return 0.0
        if low <= bpm < high:
            return 100.0
        return 40.0
    return None


def _active_weights(parts):
    weights = {}
    for name, value in WEIGHTS.items():
        if parts.get(name) is None:
            continue
        weights[name] = value
    total = sum(weights.values())
    if total <= 0:
        return {name: 1.0 / len(WEIGHTS) for name in WEIGHTS}
    return {name: value / total for name, value in weights.items()}


def score_track(query, track):
    tags = track.get("tags") or {}
    parts = {
        "mood": _overlap_score(query.get("mood"), tags.get("mood")),
        "scene": _overlap_score(query.get("scene"), tags.get("scene")),
        "relationship": _overlap_score(query.get("relationship"), tags.get("relationship")),
        "drama_function": _overlap_score(
            query.get("drama_function"),
            tags.get("drama_function"),
        ),
        "energy": _level_score(query.get("energy"), track.get("energy")),
        "tempo": _tempo_score(query, track.get("bpm")),
    }
    weights = _active_weights(parts)
    overall = 0.0
    for name, weight in weights.items():
        overall += weight * (parts[name] or 0.0)
    overall = round(overall, 1)
    mood_ok = parts["mood"] is None or parts["mood"] > 0
    strong = overall >= STRONG_OVERALL and mood_ok
    return {
        "overall": overall,
        "parts": {name: parts[name] for name in WEIGHTS},
        "strong": strong,
    }


def rank_tracks(query, tracks):
    scored = []
    for track in tracks:
        if not track.get("audio_path"):
            continue
        result = score_track(query, track)
        scored.append({"track": track, **result})
    scored.sort(
        key=lambda item: (
            item["overall"],
            (item["parts"]["mood"] or 0),
            (item["parts"]["drama_function"] or 0),
            (item["parts"]["scene"] or 0),
        ),
        reverse=True,
    )
    strong = [item for item in scored if item["strong"]]
    if strong:
        return "top", strong[:TOP_LIMIT]
    return "closest", scored[:CLOSEST_LIMIT]


def missing_label_hint(query):
    bits = []
    for name in ("mood", "scene", "relationship", "drama_function"):
        if query.get(name):
            bits.append(" / ".join(query[name]))
    if query.get("energy"):
        bits.append("{} energy".format(query["energy"]))
    return " / ".join(bits) if bits else "this scene"
