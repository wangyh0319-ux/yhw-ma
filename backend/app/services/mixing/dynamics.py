import librosa
import numpy as np

from app.services.mixing.loudness import _block_lufs, _k_weighted, _round


def _to_db(value: float):
    return 20.0 * np.log10(max(value, 1e-12))


def measure_dynamics(samples: np.ndarray, sr: int) -> dict:
    mix = samples.mean(axis=1)
    peak = float(np.max(np.abs(mix)))
    rms = float(np.sqrt(np.mean(np.square(mix))))
    peak_db = _to_db(peak)
    rms_db = _to_db(rms)

    crest_factor = float(peak / max(rms, 1e-12))
    crest_factor_db = peak_db - rms_db

    rms_frames = librosa.feature.rms(y=mix)[0]
    rms_frames = rms_frames[rms_frames > 1e-8]
    if rms_frames.size >= 4:
        low = float(np.percentile(rms_frames, 10))
        high = float(np.percentile(rms_frames, 95))
        dynamic_range_db = _to_db(high) - _to_db(low)
    else:
        dynamic_range_db = None

    short_term = _block_lufs(_k_weighted(samples, sr), sr, window_sec=3.0, hop_sec=0.1)
    if len(short_term) >= 2:
        short_term_range_lufs = _round(max(short_term) - min(short_term))
    else:
        short_term_range_lufs = None

    return {
        "sample_peak": round(peak, 6),
        "sample_peak_db": _round(peak_db),
        "rms": round(rms, 6),
        "rms_db": _round(rms_db),
        "crest_factor": round(crest_factor, 3),
        "crest_factor_db": _round(crest_factor_db),
        "peak_to_rms_db": _round(peak_db - rms_db),
        "dynamic_range_db": _round(dynamic_range_db),
        "short_term_range_lufs": short_term_range_lufs,
    }