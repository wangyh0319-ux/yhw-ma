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
    "Ballad",
    "R&B",
    "Cinematic",
    "Orchestral",
    "Ambient",
    "Piano",
    "Acoustic",
    "Folk",
    "GuFeng",
    "Electronic",
    "SynthPop",
    "LoFi",
    "Indie",
    "Rock",
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
    "Ballad": "抒情",
    "R&B": "R&B",
    "Cinematic": "影视",
    "Orchestral": "管弦",
    "Ambient": "氛围",
    "Piano": "钢琴",
    "Acoustic": "原声",
    "Folk": "民谣",
    "GuFeng": "古风",
    "Electronic": "电子",
    "SynthPop": "合成流行",
    "LoFi": "LoFi",
    "Indie": "独立",
    "Rock": "摇滚",
    "HipHop": "说唱",
}

DRAMA_FUNCTION_LABELS = {
    "Setup": "铺垫",
    "Build-up": "推进",
    "Conflict": "冲突",
    "Reveal": "揭示",
    "Twist": "反转",
    "Climax": "高潮",
    "Transition": "转场",
    "Memory": "回忆",
    "Ending": "结尾",
}

RELATIONSHIP_LABELS = {
    "FirstMeeting": "初遇",
    "Crush": "暗恋",
    "Flirting": "暧昧",
    "Misunderstanding": "误会",
    "ColdWar": "冷战",
    "Breakup": "分手",
    "Reunion": "重逢",
    "Confession": "告白",
    "Betrayal": "背叛",
    "Reconciliation": "和好",
}

SCENE_LABELS = {
    "Rain": "雨",
    "Night": "夜",
    "Street": "街",
    "Home": "家",
    "Hospital": "医院",
    "Office": "公司",
    "Cafe": "咖啡馆",
    "Campus": "校园",
    "Airport": "机场",
    "Wedding": "婚礼",
    "Alone": "独处",
}

ENERGY_LABELS = {
    "Low": "低",
    "Medium": "中",
    "High": "高",
}

TEMPO_FEEL_LABELS = {
    "Slow": "慢",
    "Moderate": "中速",
    "Driving": "推动",
}


def _labeled(ids, labels):
    return [{"id": item, "label": labels[item]} for item in ids]


def taxonomy_payload():
    return {
        "mood": _labeled(MOOD, MOOD_LABELS),
        "style": _labeled(GENRE, STYLE_LABELS),
        "drama_function": _labeled(DRAMA_FUNCTION, DRAMA_FUNCTION_LABELS),
        "relationship": _labeled(RELATIONSHIP, RELATIONSHIP_LABELS),
        "scene": _labeled(SCENE, SCENE_LABELS),
        "energy": _labeled(ENERGY, ENERGY_LABELS),
        "tempo_feel": _labeled(TEMPO_FEEL, TEMPO_FEEL_LABELS),
        "tension": _labeled(LEVEL, ENERGY_LABELS),
        "intensity": _labeled(LEVEL, ENERGY_LABELS),
    }