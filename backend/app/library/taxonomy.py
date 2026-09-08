MOOD = (
    "Warm",
    "Sad",
    "Oppressive",
    "Romantic",
    "Lonely",
    "Angry",
    "Tense",
    "Healing",
    "Relieved",
    "Nostalgic",
    "Melancholic",
    "Flirty",
)

DRAMA_FUNCTION = (
    "Setup",
    "Build-up",
    "Conflict",
    "Reveal",
    "Twist",
    "Climax",
    "Transition",
    "Memory",
    "Ending",
)

RELATIONSHIP = (
    "FirstMeeting",
    "Crush",
    "Flirting",
    "Misunderstanding",
    "ColdWar",
    "Breakup",
    "Reunion",
    "Confession",
    "Betrayal",
    "Reconciliation",
)

SCENE = (
    "Rain",
    "Night",
    "Street",
    "Home",
    "Hospital",
    "Office",
    "Cafe",
    "Campus",
    "Airport",
    "Wedding",
    "Alone",
)

GENRE = (
    "Pop",
    "R&B",
    "Cinematic",
    "Ambient",
    "Rock",
    "Folk",
    "Electronic",
    "HipHop",
)

VOCAL_TYPE = ("Instrumental", "Male", "Female", "Duo", "Mixed")
ENERGY = ("Low", "Medium", "High")
TEMPO_FEEL = ("Slow", "Moderate", "Driving")
LEVEL = ("Low", "Medium", "High")

NAMESPACES = {
    "mood": MOOD,
    "style": GENRE,
    "drama_function": DRAMA_FUNCTION,
    "relationship": RELATIONSHIP,
    "scene": SCENE,
}

MOOD_LABELS = {
    "Warm": "温暖",
    "Sad": "悲伤",
    "Oppressive": "压抑",
    "Romantic": "浪漫",
    "Lonely": "孤独",
    "Angry": "愤怒",
    "Tense": "紧张",
    "Healing": "治愈",
    "Relieved": "释然",
    "Nostalgic": "怀念",
    "Melancholic": "忧伤",
    "Flirty": "暧昧",
}

STYLE_LABELS = {
    "Pop": "流行",
    "R&B": "R&B",
    "Cinematic": "影视",
    "Ambient": "氛围",
    "Rock": "摇滚",
    "Folk": "民谣",
    "Electronic": "电子",
    "HipHop": "说唱",
}


def taxonomy_payload():
    return {
        "mood": [{"id": item, "label": MOOD_LABELS[item]} for item in MOOD],
        "style": [{"id": item, "label": STYLE_LABELS[item]} for item in GENRE],
    }