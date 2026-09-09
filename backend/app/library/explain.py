def template_reason(scene, query, track, parts):
    tags = track.get("tags") or {}
    mood = "、".join(tags.get("mood") or []) or "未标注情绪"
    energy = track.get("energy") or "未知"
    bpm = track.get("bpm")
    tempo = "{} BPM".format(bpm) if bpm is not None else "节奏未测"
    asked = "、".join((query.get("mood") or [])[:3]) or "该剧情"
    return (
        "《{title}》现有标签为{mood}，能量{energy}，{tempo}。"
        "这与你描述的「{asked}」有重叠；匹配分来自曲库标签和 Analyzer 的 BPM/能量，没有另编情节。"
        "剧情摘要：{scene}"
    ).format(
        title=track.get("title") or "这首",
        mood=mood,
        energy=energy,
        tempo=tempo,
        asked=asked,
        scene=(scene or "")[:80],
    )


def explain_matches(scene, query, matches):
    filled = []
    for item in matches:
        copy = dict(item)
        copy["reason"] = template_reason(scene, query, item["track"], item["parts"])
        filled.append(copy)
    return filled
