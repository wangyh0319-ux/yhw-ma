import numpy as np

from app.services.mixing.loudness import _round, _true_peak_dbtp

SAMPLE_CLIP_LEVEL = 0.999
HIGH_SAMPLE_PEAK_DB = -0.1
TRUE_PEAK_CEILING_DBTP = -1.0


def measure_clipping(samples: np.ndarray, sr: int) -> dict:
    peak = float(np.max(np.abs(samples)))
    peak_db = 20.0 * np.log10(max(peak, 1e-12))
    clip_count = int(np.sum(np.abs(samples) >= SAMPLE_CLIP_LEVEL))
    total = int(samples.size)
    true_peak_dbtp = _true_peak_dbtp(samples)

    clipped = bool(clip_count > 0)
    high_sample_peak = bool(peak_db > HIGH_SAMPLE_PEAK_DB)
    high_true_peak = bool(true_peak_dbtp is not None and true_peak_dbtp > TRUE_PEAK_CEILING_DBTP)

    return {
        "true_peak_dbtp": true_peak_dbtp,
        "sample_peak_db": _round(peak_db),
        "clip_sample_count": clip_count,
        "clip_ratio": round(clip_count / max(total, 1), 6),
        "clipped": clipped,
        "high_sample_peak": high_sample_peak,
        "high_true_peak": high_true_peak,
        "true_peak_ceiling_dbtp": TRUE_PEAK_CEILING_DBTP,
    }