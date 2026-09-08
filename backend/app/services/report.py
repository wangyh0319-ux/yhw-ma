from datetime import datetime, timezone


def _duration_label(seconds: float) -> str:
    total = max(0, int(round(seconds)))
    return f"{total // 60}:{total % 60:02d}"


def _build_summary(metrics: dict, ai: dict) -> str:
    lufs = metrics["lufs"]
    loudness = f"LUFS {lufs:.1f}" if isinstance(lufs, (int, float)) else "LUFS n/a"
    parts = [
        metrics["key"],
        f"{metrics['bpm']:.1f} BPM",
        _duration_label(metrics["duration_sec"]),
        loudness,
        f"DR {metrics['dynamic_range_db']:.1f} dB",
    ]
    if ai.get("available") and ai.get("genre"):
        mood = ai.get("mood") or "unlabeled mood"
        parts.append(f"{ai['genre']} / {mood}")
    return " · ".join(parts)


def build_report(saved: dict, analysis: dict, ai: dict) -> dict:
    metrics = {
        "duration_sec": analysis["duration_sec"],
        "sample_rate": analysis["sample_rate"],
        "bpm": analysis["bpm"],
        "key": analysis["key"],
        "lufs": analysis["lufs"],
        "rms": analysis["rms"],
        "rms_db": analysis["rms_db"],
        "peak_db": analysis["peak_db"],
        "dynamic_range_db": analysis["dynamic_range_db"],
    }
    return {
        "file": {
            "filename": saved["filename"],
            "size_bytes": saved["size_bytes"],
            "content_type": saved["content_type"],
        },
        "metrics": metrics,
        "spectrum": analysis["spectrum"],
        "ai": ai,
        "summary": _build_summary(metrics, ai),
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
    }