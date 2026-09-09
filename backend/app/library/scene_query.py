from app.library.taxonomy import (
    ENERGY,
    LEVEL,
    NAMESPACES,
    TEMPO_FEEL,
    taxonomy_payload,
)

LIST_FIELDS = ("mood", "scene", "relationship", "drama_function")
SINGLE_FIELDS = {
    "energy": ENERGY,
    "tension": LEVEL,
    "intensity": LEVEL,
    "tempo_feel": TEMPO_FEEL,
}

# Map wording from the product spec onto existing English IDs only.
ALIASES = {
    "mood": {},
    "scene": {
        "Taxi": "Street",
        "RainyNight": "Night",
    },
    "relationship": {
        "MissedConnection": "Reunion",
        "Missed Connection": "Reunion",
    },
    "drama_function": {
        "Emotional Build-up": "Build-up",
        "Emotional Aftermath": "Ending",
        "Buildup": "Build-up",
    },
}


def empty_scene_query():
    return {
        "mood": [],
        "scene": [],
        "relationship": [],
        "drama_function": [],
        "energy": None,
        "tension": None,
        "intensity": None,
        "tempo_feel": None,
        "tempo_range": None,
        "dropped": [],
    }


def scene_query_schema():
    payload = taxonomy_payload()
    return {
        "fields": {
            "mood": "list, from taxonomy.mood",
            "scene": "list, from taxonomy.scene",
            "relationship": "list, from taxonomy.relationship",
            "drama_function": "list, from taxonomy.drama_function",
            "energy": "one of Low|Medium|High",
            "tension": "one of Low|Medium|High",
            "intensity": "one of Low|Medium|High",
            "tempo_feel": "one of Slow|Moderate|Driving",
            "tempo_range": "[min_bpm, max_bpm] or null",
        },
        "allowed": {
            "mood": payload["mood"],
            "scene": payload["scene"],
            "relationship": payload["relationship"],
            "drama_function": payload["drama_function"],
            "energy": payload["energy"],
            "tension": payload["tension"],
            "intensity": payload["intensity"],
            "tempo_feel": payload["tempo_feel"],
        },
        "empty": empty_scene_query(),
    }


def _as_list(value):
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return list(value)
    return [value]


def _keep_list(namespace, values, dropped):
    allowed = set(NAMESPACES[namespace])
    aliases = ALIASES.get(namespace) or {}
    cleaned = []
    for raw in _as_list(values):
        item = raw if isinstance(raw, str) else str(raw)
        mapped = aliases.get(item, item)
        if mapped in allowed and mapped not in cleaned:
            cleaned.append(mapped)
        elif mapped not in allowed:
            dropped.append({"field": namespace, "value": item})
    return cleaned[:4]


def _keep_one(field, value, allowed, dropped):
    if value is None or value == "":
        return None
    if not isinstance(value, str):
        dropped.append({"field": field, "value": value})
        return None
    if value in allowed:
        return value
    dropped.append({"field": field, "value": value})
    return None


def _keep_tempo_range(value, dropped):
    if value is None or value == "":
        return None
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        dropped.append({"field": "tempo_range", "value": value})
        return None
    try:
        low = float(value[0])
        high = float(value[1])
    except (TypeError, ValueError):
        dropped.append({"field": "tempo_range", "value": value})
        return None
    if high < low:
        low, high = high, low
    low = max(40.0, min(220.0, low))
    high = max(40.0, min(220.0, high))
    return [round(low, 1), round(high, 1)]


def sanitize_scene_query(payload):
    source = payload if isinstance(payload, dict) else {}
    dropped = []
    query = empty_scene_query()
    for name in LIST_FIELDS:
        query[name] = _keep_list(name, source.get(name), dropped)
    for field, allowed in SINGLE_FIELDS.items():
        query[field] = _keep_one(field, source.get(field), allowed, dropped)
    query["tempo_range"] = _keep_tempo_range(source.get("tempo_range"), dropped)
    query["dropped"] = dropped
    return query
