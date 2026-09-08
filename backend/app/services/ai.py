import json

import httpx

from app.config import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL

SKIPPED = {
    "available": False,
    "genre": None,
    "mood": None,
    "energy": None,
    "energy_label": None,
    "reason": None,
}


def classify_track(analysis: dict) -> dict:
    if not OPENAI_API_KEY:
        return {
            **SKIPPED,
            "message": "Set OPENAI_API_KEY in backend/.env to enable AI labels.",
        }

    summary = {
        "bpm": analysis.get("bpm"),
        "key": analysis.get("key"),
        "duration_sec": analysis.get("duration_sec"),
        "lufs": analysis.get("lufs"),
        "rms_db": analysis.get("rms_db"),
        "peak_db": analysis.get("peak_db"),
        "dynamic_range_db": analysis.get("dynamic_range_db"),
        "spectrum_bands": analysis.get("spectrum", {}).get("bands"),
    }

    payload = {
        "model": OPENAI_MODEL,
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
        "messages": [
            {
                "role": "system",
                "content": (
                    "You classify music from objective audio measurements only. "
                    "Return JSON with keys: genre, mood, energy (0-100 integer), "
                    "energy_label (Low, Medium, or High), reason (one short sentence). "
                    "Do not invent details that the numbers cannot support."
                ),
            },
            {
                "role": "user",
                "content": json.dumps(summary),
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
            timeout=30.0,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        parsed = json.loads(content)
    except Exception:
        return {
            **SKIPPED,
            "message": "AI request failed. Objective metrics are still available.",
        }

    energy = parsed.get("energy")
    try:
        energy = max(0, min(100, int(energy)))
    except (TypeError, ValueError):
        energy = None

    return {
        "available": True,
        "genre": parsed.get("genre"),
        "mood": parsed.get("mood"),
        "energy": energy,
        "energy_label": parsed.get("energy_label"),
        "reason": parsed.get("reason"),
        "message": None,
    }