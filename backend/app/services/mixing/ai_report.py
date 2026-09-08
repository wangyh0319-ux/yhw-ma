import json

import httpx

from app.config import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL

SKIPPED = {
    "available": False,
    "overall_assessment": None,
    "frequency_balance": None,
    "dynamics": None,
    "loudness": None,
    "stereo_image": None,
    "clipping_peak": None,
    "priority_issues": [],
    "suggested_actions": [],
    "what_already_works": [],
}

SECTIONS = (
    "overall_assessment",
    "frequency_balance",
    "dynamics",
    "loudness",
    "stereo_image",
    "clipping_peak",
)


def _compact(analysis: dict) -> dict:
    frequency = analysis.get("frequency") or {}
    return {
        "duration_sec": analysis.get("duration_sec"),
        "channels": analysis.get("channels"),
        "loudness": analysis.get("loudness"),
        "frequency_bands": frequency.get("bands"),
        "dynamics": analysis.get("dynamics"),
        "stereo": analysis.get("stereo"),
        "clipping": analysis.get("clipping"),
        "scores": analysis.get("scores"),
    }


def write_mix_report(analysis: dict) -> dict:
    if not OPENAI_API_KEY:
        return {
            **SKIPPED,
            "message": "Set OPENAI_API_KEY in backend/.env to enable the AI mixing report.",
        }

    payload = {
        "model": OPENAI_MODEL,
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a mixing assistant. You do not hear audio. "
                    "Use only the JSON measurements, scores, and issues. "
                    "Treat scores.issues as the only confirmed problems. "
                    "Do not invent frequency problems, EQ Hz, or Q values. "
                    "If stereo.available is false, say stereo cannot be judged. "
                    "Advice may name bands and a gentle 1–2 dB starting range, "
                    "never absolute EQ settings. "
                    "Return JSON with keys: overall_assessment, frequency_balance, "
                    "dynamics, loudness, stereo_image, clipping_peak "
                    "(each a short paragraph), plus priority_issues, "
                    "suggested_actions, what_already_works (arrays of strings)."
                ),
            },
            {
                "role": "user",
                "content": json.dumps(_compact(analysis)),
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
        return {
            **SKIPPED,
            "message": "AI mixing report failed. Objective scores are still available.",
        }

    report = {**SKIPPED, "available": True, "message": None}
    for key in SECTIONS:
        value = parsed.get(key)
        report[key] = value if isinstance(value, str) else None
    for key in ("priority_issues", "suggested_actions", "what_already_works"):
        value = parsed.get(key)
        if isinstance(value, list):
            report[key] = [str(item) for item in value]
        else:
            report[key] = []
    return report