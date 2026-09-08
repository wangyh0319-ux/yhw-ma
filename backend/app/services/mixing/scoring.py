STREAMING_LUFS = -14.0
HOT_LUFS = -9.0
VERY_HOT_LUFS = -8.0


def _clamp(score: float) -> int:
    return int(max(0, min(100, round(score))))


def _band(frequency: dict, name: str):
    return frequency.get("bands", {}).get(name) or {}


def _rel(frequency: dict, name: str):
    data = _band(frequency, name)
    if not data.get("available"):
        return None
    return data.get("relative_to_mid_db")


def _is_narrowband(frequency: dict) -> bool:
    energetic = 0
    for name in ("sub", "bass", "low_mid", "upper_mid", "presence", "air"):
        relative = _rel(frequency, name)
        if relative is not None and relative > -12:
            energetic += 1
    return energetic < 2


def _issue(priority, code, title, detail, range_label=None, evidence=None):
    return {
        "priority": priority,
        "code": code,
        "title": title,
        "range": range_label,
        "detail": detail,
        "evidence": evidence or {},
    }


def _score_loudness(loudness: dict, clipping: dict):
    score = 100.0
    issues = []
    lufs = loudness.get("integrated_lufs")
    true_peak = clipping.get("true_peak_dbtp")

    if lufs is None:
        return None, issues

    score -= min(abs(lufs - STREAMING_LUFS) * 3.0, 30)
    if lufs > VERY_HOT_LUFS:
        score -= 20
        issues.append(
            _issue(
                "high",
                "hot_loudness",
                "Master Loudness",
                f"Integrated LUFS is {lufs}, which is very hot versus a typical -14 LUFS streaming target.",
                evidence={"integrated_lufs": lufs, "true_peak_dbtp": true_peak},
            )
        )
    elif lufs > HOT_LUFS:
        score -= 10
        issues.append(
            _issue(
                "medium",
                "hot_loudness",
                "Master Loudness",
                f"Integrated LUFS is {lufs}. Check limiter gain if this was meant for streaming.",
                evidence={"integrated_lufs": lufs, "true_peak_dbtp": true_peak},
            )
        )

    if clipping.get("clipped"):
        score -= 25
        issues.append(
            _issue(
                "high",
                "clipping",
                "Clipping",
                "Samples hit digital full scale. Check limiter/clipper output.",
                evidence={"clip_sample_count": clipping.get("clip_sample_count")},
            )
        )
    elif clipping.get("high_true_peak"):
        score -= 12
        issues.append(
            _issue(
                "high",
                "high_true_peak",
                "True Peak",
                f"True Peak is {true_peak} dBTP, above the {clipping.get('true_peak_ceiling_dbtp')} dBTP ceiling.",
                evidence={"true_peak_dbtp": true_peak},
            )
        )
    elif clipping.get("high_sample_peak"):
        score -= 8
        issues.append(
            _issue(
                "medium",
                "high_sample_peak",
                "High Sample Peak",
                "Sample peak is very close to 0 dBFS.",
                evidence={"sample_peak_db": clipping.get("sample_peak_db")},
            )
        )

    return _clamp(score), issues


def _score_frequency(frequency: dict):
    score = 100.0
    issues = []
    if _is_narrowband(frequency):
        return _clamp(score), issues

    checks = (
        ("low_mid", 6, 8, "120–300Hz", "Low-Mid Energy", "low_mid_buildup"),
        ("bass", 8, 10, "60–120Hz", "Bass Energy", "bass_buildup"),
        ("sub", 10, 12, "20–60Hz", "Sub Energy", "sub_buildup"),
        ("upper_mid", 8, 10, "1–4kHz", "Upper Mid Energy", "upper_mid_buildup"),
        ("presence", 8, 10, "4–8kHz", "Presence Energy", "presence_buildup"),
    )
    for name, medium, high, range_label, title, code in checks:
        relative = _rel(frequency, name)
        if relative is None:
            continue
        if relative >= high:
            score -= 18
            issues.append(
                _issue(
                    "high",
                    code,
                    title,
                    f"{range_label} energy is {relative} dB above mid. This can cause mix congestion.",
                    range_label,
                    {"relative_to_mid_db": relative},
                )
            )
        elif relative >= medium:
            score -= 10
            issues.append(
                _issue(
                    "medium",
                    code,
                    title,
                    f"{range_label} energy is {relative} dB above mid.",
                    range_label,
                    {"relative_to_mid_db": relative},
                )
            )
    return _clamp(score), issues


def _score_dynamics(dynamics: dict, loudness: dict, frequency: dict):
    score = 100.0
    issues = []
    crest = dynamics.get("crest_factor_db")
    if crest is None:
        return None, issues

    if crest < 4:
        score -= 28
    elif crest < 6:
        score -= 14
    elif crest < 8:
        score -= 6

    dr = dynamics.get("dynamic_range_db")
    if dr is not None and dr < 2:
        score -= 16
    elif dr is not None and dr < 4:
        score -= 8

    lufs = loudness.get("integrated_lufs")
    loud_enough = lufs is not None and lufs > -18
    if loud_enough and not _is_narrowband(frequency) and crest < 5:
        priority = "high" if crest < 4 else "medium"
        issues.append(
            _issue(
                priority,
                "low_crest",
                "Low Crest Factor",
                f"Crest factor is {crest} dB on a loud mix, which often means heavy limiting.",
                evidence={"crest_factor_db": crest, "integrated_lufs": lufs},
            )
        )
    return _clamp(score), issues


def _score_stereo(stereo: dict):
    if not stereo.get("available"):
        return None, []

    score = 100.0
    issues = []
    balance = stereo.get("lr_balance_db")
    correlation = stereo.get("correlation")
    low = stereo.get("low_frequency") or {}

    if correlation is not None and correlation < 0:
        score -= 30
        issues.append(
            _issue(
                "high",
                "out_of_phase",
                "Stereo Correlation",
                f"Left/right correlation is {correlation}. Check for inverted polarity or excessive out-of-phase content.",
                evidence={"correlation": correlation},
            )
        )

    if balance is not None and abs(balance) >= 4.5:
        score -= 16
        issues.append(
            _issue(
                "medium" if abs(balance) < 7 else "high",
                "lr_imbalance",
                "Left / Right Balance",
                f"Left is {balance} dB relative to right (positive = left louder).",
                evidence={"lr_balance_db": balance},
            )
        )

    low_side = low.get("side_to_mid_db")
    if low_side is not None and low_side > -6:
        score -= 14
        issues.append(
            _issue(
                "medium",
                "low_stereo",
                "Low-Frequency Stereo",
                f"Below 120Hz, side-to-mid is {low_side} dB. Bass may not be solid in mono.",
                "20–120Hz",
                {"side_to_mid_db": low_side},
            )
        )
    return _clamp(score), issues


def score_mix(analysis: dict) -> dict:
    loudness_score, loudness_issues = _score_loudness(
        analysis["loudness"], analysis["clipping"]
    )
    frequency_score, frequency_issues = _score_frequency(analysis["frequency"])
    dynamics_score, dynamics_issues = _score_dynamics(
        analysis["dynamics"], analysis["loudness"], analysis["frequency"]
    )
    stereo_score, stereo_issues = _score_stereo(analysis["stereo"])

    parts = [
        ("loudness", loudness_score, loudness_issues),
        ("frequency", frequency_score, frequency_issues),
        ("dynamics", dynamics_score, dynamics_issues),
        ("stereo", stereo_score, stereo_issues),
    ]
    available_scores = [score for _, score, _ in parts if score is not None]
    overall = _clamp(sum(available_scores) / len(available_scores)) if available_scores else None

    issues = loudness_issues + frequency_issues + dynamics_issues + stereo_issues
    priority_rank = {"high": 0, "medium": 1}
    issues.sort(key=lambda item: priority_rank.get(item["priority"], 9))

    looks_good = []
    labels = {
        "loudness": "Loudness",
        "frequency": "Frequency Balance",
        "dynamics": "Dynamic Range",
        "stereo": "Stereo Balance",
    }
    for name, score, category_issues in parts:
        if score is not None and score >= 80 and not category_issues:
            looks_good.append(labels[name])

    if analysis["stereo"].get("available") is False:
        looks_good = [item for item in looks_good if item != "Stereo Balance"]

    return {
        "overall": overall,
        "loudness": loudness_score,
        "frequency": frequency_score,
        "dynamics": dynamics_score,
        "stereo": stereo_score,
        "issues": issues,
        "looks_good": looks_good,
    }